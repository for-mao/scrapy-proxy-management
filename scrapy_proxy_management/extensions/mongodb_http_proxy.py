import re
from collections import defaultdict
from functools import partial
from itertools import starmap
from operator import methodcaller
from typing import Callable
from typing import Dict
from typing import Iterator
from typing import List
from typing import Set
from typing import Tuple
from urllib.parse import splitport
from urllib.parse import urlparse

from pymongo import MongoClient
from pymongo.collection import Collection as CollectionSync
from pymongo.database import Database as DatabaseSync
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.spiders import Spider
from scrapy.utils.misc import load_object

from . import BaseProxyStorage
from . import basic_auth_header
from ..extensions.strategies import BaseProxyManagementStrategy


def get_proxy_from_doc(
        doc: Dict, orig_type: str, auth_encoding: str
) -> Tuple[bytes, str]:
    credentials = basic_auth_header(
        doc['username'], doc.get('password', ''), auth_encoding
    ) if doc.get('username') else None

    proxy_url: str = doc['proxy']

    return credentials, proxy_url


class MongoDBSyncProxyStorage(BaseProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str, mw):
        super().__init__(settings, auth_encoding, mw)

        self.mongodb_settings: Dict = dict(starmap(
            lambda k, v: (k.replace('HTTPPROXY_MONGODB_', '').lower(), v),
            filter(lambda x: x[0].startswith('HTTPPROXY_MONGODB_'),
                   self.settings.items())
        ))

        self.not_mongoclient_parameters = self.mongodb_settings.get(
            'not_mongoclient_parameters'
        )

        self.conn: MongoClient = None
        self.db: DatabaseSync = None
        self.coll: CollectionSync = None

        self.strategy: BaseProxyManagementStrategy = load_object(
            self.mongodb_settings['proxy_management_strategy']
        ).from_crawler(settings=self.settings, proxy_storage=self)

        self._proxy_retriever: methodcaller = methodcaller(
            self.mongodb_settings['proxy_retriever'].pop('name'),
            **self.mongodb_settings['proxy_retriever']
        )
        self._get_proxy_from_doc: Callable = partial(
            load_object(self.mongodb_settings['get_proxy_from_doc']),
            auth_encoding=self.auth_encoding
        )

        self._proxies: Dict[str, List[Tuple[bytes, str]]] = None
        self.proxies: Dict[str, Iterator[Tuple[bytes, str], None, None]] = None
        self.invalidate_proxies: Set[Tuple[str, bytes, str]] = set()

    def open_spider(self, spider: Spider):
        self.conn: MongoClient = MongoClient(**{
            **self._prepare_conn_args(), 'appname': spider.name
        })

        self.db = self.conn.get_database(self.mongodb_settings['database'])
        self.coll = self.db.get_collection(self.mongodb_settings['collection'])

        self.strategy.open_spider()

        if self.mongodb_settings.get('username'):
            self.log.info(
                'Proxy storage in MongoDB database %s is open, '
                'authorized by %s.',
                self.mongodb_settings['authsource'],
                self.mongodb_settings['username']
            )
        else:
            self.log.info(
                'Proxy storage in MongoDB database %s is open.',
                self.mongodb_settings['authsource'],
            )

    def close_spider(self, spider: Spider):
        self.strategy.close_spider()
        self.conn.close()

    def invalidate_proxy(self, spider: Spider, request: Request, **kwargs):
        self.strategy.invalidate_proxy(
            request.meta['proxy'],
            urlparse(request.url).scheme,
            request.headers.get('Proxy-Authorization'),
        )

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        """Test if proxies should not be used for a particular host.

        Checks the proxy dict for the value of no_proxy, which should
        be a list of comma separated DNS suffixes, or '*' for all hosts.

        """
        if proxies is None:
            proxies = self._proxies

        # don't bypass, if no_proxy isn't specified
        try:
            no_proxy: List = proxies['no']
        except KeyError:
            return False

        # '*' is special case for always bypass
        if '*' in no_proxy:
            return True

        # strip port off host
        host_only, port = splitport(host)

        for pattern in no_proxy:
            if any(map(lambda x: pattern.match(x), [host_only, host])):
                return True

        # otherwise, don't bypass
        return False

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        try:
            return next(self.proxies[scheme])
        except StopIteration:
            self.strategy.reload_proxies()
            return next(self.proxies[scheme])

    def _get_proxies(self) -> Dict[str, List[Tuple[bytes, str]]]:
        _proxies = defaultdict(list)

        docs_proxies = self._proxy_retriever(self.coll)
        for doc_proxy in docs_proxies:
            scheme = doc_proxy['scheme']
            if scheme != 'no':
                proxy = self._get_proxy_from_doc(doc_proxy, '')
                _proxies[scheme].append(proxy)
            elif scheme == 'no':
                _proxies[scheme].append(
                    doc_proxy['proxy']
                    if doc_proxy['proxy'] == '*'
                    else re.compile(r'(.+\.)?{}$'.format(
                        re.escape(doc_proxy['proxy'].lstrip('.'))
                    ), flags=re.IGNORECASE))

        return _proxies

    def _load_proxies(self):
        self._proxies = self._get_proxies()
        self.proxies = dict(starmap(
            lambda k, v: (k, iter(v)), self._proxies.items()
        ))

    def _prepare_conn_args(self) -> Dict:
        return dict(filter(
            lambda x: x[0] not in self.not_mongoclient_parameters,
            self.mongodb_settings.items()
        ))
