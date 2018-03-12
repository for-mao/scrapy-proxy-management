import logging
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
from urllib.parse import urlunparse

from pymongo import MongoClient
from pymongo.collection import Collection as CollectionSync
from pymongo.database import Database as DatabaseSync
from scrapy.http import Request, Response
from scrapy.settings import SETTINGS_PRIORITIES
from scrapy.settings import Settings
from scrapy.spiders import Spider
from scrapy.utils.misc import load_object

from . import BaseProxyStorage
from . import basic_auth_header
from ..extensions.strategies import BaseProxyManagementStrategy
from ..utils import unfreeze_settings

logger = logging.getLogger(__name__)


def get_proxy_from_doc(
        doc: Dict, orig_type: str, auth_encoding: str
) -> Tuple[bytes, str]:
    credentials = basic_auth_header(
        doc['username'], doc.get('password', ''), auth_encoding
    ) if doc.get('username') else None

    proxy_url: str = doc['proxy']

    return credentials, proxy_url


def get_proxy_from_doc_2(
        doc: Dict, orig_type: str, auth_encoding: str
) -> Tuple[bytes, str]:
    credentials = basic_auth_header(
        doc['username'], doc.get('password', ''), auth_encoding
    ) if doc.get('username') else None

    proxy_url: str = urlunparse((
        doc['scheme'], '{}:{}'.format(doc['ip'], str(doc['port'])),
        '', '', '', ''
    ))

    return credentials, proxy_url


class MongoDBSyncProxyStorage(BaseProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str, mw):
        super().__init__(settings, auth_encoding, mw)

        self.mongodb_settings: Dict = self._get_mongodb_settings()

        self.not_mongoclient_parameters = self.mongodb_settings.get(
            'not_mongoclient_parameters'
        )

        self.uri: str = None
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
        self.proxies_invalidated: Set[Tuple[str, bytes, str]] = set()

    def open_spider(self, spider: Spider):
        self.conn: MongoClient = MongoClient(**{
            **self._prepare_conn_args(), 'appname': spider.name
        })

        self.uri = urlunparse((
            'mongodb', ':'.join(map(lambda x: str(x), self.conn.address)),
            '', '', '', ''
        ))
        self.db = self.conn.get_database(self.mongodb_settings['database'])
        self.coll = self.db.get_collection(self.mongodb_settings['collection'])

        self.strategy.open_spider()

        if self.mongodb_settings.get('username'):
            logger.info(
                '%s (%s) is opened with authSource "%s", authorized by "%s"',
                self.__class__.__name__,
                self.uri,
                self.mongodb_settings['authsource'],
                self.mongodb_settings['username']
            )
        else:
            logger.info(
                'Proxy storage in MongoDB database %s is open',
                self.mongodb_settings['authsource'],
            )

        for scheme, proxies in self._proxies.items():
            logger.info(
                'Loaded %s %s proxies from %s (%s)',
                len(proxies),
                scheme,
                self.settings['HTTPPROXY_STORAGE'].rsplit('.', 1)[-1],
                self.uri,
            )
            self.mw.stats.set_value(
                'proxy/{scheme}'.format(scheme=scheme), len(proxies)
            )

    def close_spider(self, spider: Spider):
        self.strategy.close_spider()
        self.conn.close()
        logger.info('%s (%s) is closed', self.__class__.__name__, self.uri)

    def invalidate_proxy(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None, **kwargs
    ):
        self.strategy.invalidate_proxy(
            request, response, exception, spider, **kwargs
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
            logger.debug('Proxies for %s exhausted, reload now', scheme)

            self.strategy.reload_proxies()

            for scheme, proxies in self._proxies.items():
                logger.debug(
                    'Loaded %s %s proxies from %s (%s)',
                    len(proxies),
                    scheme,
                    self.settings['HTTPPROXY_STORAGE'].rsplit('.', 1)[-1],
                    self.uri,
                )

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

    def _get_mongodb_settings(self) -> Dict:
        if (
                self.settings.getpriority(
                    'HTTPPROXY_MONGODB_AUTHSOURCE'
                ) == SETTINGS_PRIORITIES['default']
        ):
            with unfreeze_settings(self.settings) as settings:
                self.settings.set(
                    'HTTPPROXY_MONGODB_AUTHSOURCE',
                    self.settings.get('HTTPPROXY_MONGODB_DATABASE')
                )

        return dict(starmap(
            lambda k, v: (k.replace('HTTPPROXY_MONGODB_', '').lower(), v),
            filter(lambda x: x[0].startswith('HTTPPROXY_MONGODB_'),
                   self.settings.items())
        ))
