import logging
import re
from collections import defaultdict
from functools import partial
from itertools import starmap
from operator import methodcaller
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import Tuple
from typing import Union
from urllib.parse import urlunparse

from pymongo import MongoClient
from pymongo.collection import Collection as CollectionSync
from pymongo.database import Database as DatabaseSync
from scrapy.crawler import Crawler
from scrapy.settings import SETTINGS_PRIORITIES
from scrapy.spiders import Spider
from scrapy.utils.misc import load_object

from . import BaseStorage
from ..utils import basic_auth_header
from ..utils import unfreeze_settings

logger = logging.getLogger(__name__)

pattern_credential = re.compile(rb'^Basic\s(?P<credential>.*)')


def get_proxy_from_doc(
        doc: Dict, orig_type: str, auth_encoding: str
) -> Tuple[bytes, str]:
    credentials: bytes = basic_auth_header(
        doc['username'], doc.get('password', ''), auth_encoding
    ) if doc.get('username') else None

    proxy_url: str = doc['proxy']

    return credentials, proxy_url


def get_proxy_from_doc_2(
        doc: Dict, orig_type: str, auth_encoding: str
) -> Tuple[bytes, str]:
    credentials: bytes = basic_auth_header(
        doc['username'], doc.get('password', ''), auth_encoding
    ) if doc.get('username') else None

    proxy_url: str = urlunparse((
        doc['scheme'], '{}:{}'.format(doc['ip'], str(doc['port'])),
        '', '', '', ''
    ))

    return credentials, proxy_url


class MongoDBSyncStorage(BaseStorage):
    def __init__(self, crawler: Crawler, auth_encoding: str, mw):
        super().__init__(crawler, auth_encoding, mw)

        self.mongodb_settings: Dict = self._get_mongodb_settings()

        self.not_mongoclient_parameters: Dict = self.mongodb_settings.get(
            'not_mongoclient_parameters'
        )

        self.uri: str = None
        self.conn: MongoClient = None
        self.db: DatabaseSync = None
        self.coll: CollectionSync = None

        self._proxy_retriever: methodcaller = methodcaller(
            self.mongodb_settings['proxy_retriever'].pop('name'),
            **self.mongodb_settings['proxy_retriever']
        )
        self._get_proxy_from_doc: Callable = partial(
            load_object(self.mongodb_settings['get_proxy_from_doc']),
            auth_encoding=self.auth_encoding
        )

        self.proxies_invalidated: Set[Tuple[str, bytes, str]] = set()

    def open_spider(self, spider: Spider):
        self.conn = MongoClient(**{
            **self._prepare_conn_args(), 'appname': spider.name
        })

        self.uri = urlunparse((
            'mongodb', ':'.join(map(lambda x: str(x), self.conn.address)),
            '', '', '', ''
        ))
        self.db = self.conn.get_database(self.mongodb_settings['database'])
        self.coll = self.db.get_collection(self.mongodb_settings['collection'])

        if self.mongodb_settings.get('username'):
            logger.info(
                '%s (%s) is opened with authSource "%s", authorized by "%s"',
                self.__class__.__name__, self.uri,
                self.mongodb_settings['authsource'],
                self.mongodb_settings['username']
            )
        else:
            logger.info(
                'Proxy storage in MongoDB database %s is open',
                self.mongodb_settings['authsource'],
            )

        self.proxies = self.load_proxies()

        for scheme, proxies in self.proxies.items():
            logger.info(
                '%s (%s) loads %s %s proxies',
                self.settings['HTTPPROXY_STORAGE'].rsplit('.', 1)[-1],
                self.uri, len(proxies), scheme,
            )
            self.mw.stats.set_value(
                'proxy/{scheme}'.format(scheme=scheme), len(proxies)
            )

    def close_spider(self, spider: Spider):
        self.conn.close()
        logger.info('%s (%s) is closed', self.__class__.__name__, self.uri)

    def load_proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        proxies: DefaultDict = defaultdict(list)

        docs: Iterable[Dict] = self._proxy_retriever(self.coll)

        for doc in docs:
            scheme: str = doc['scheme']
            if scheme != 'no':
                proxy: Tuple[bytes, str] = self._get_proxy_from_doc(doc, '')
                proxies[scheme].append(proxy)
            elif scheme == 'no':
                if doc['proxy'] == '*':
                    proxy: str = doc['proxy']
                    proxies[scheme].append(proxy)
                else:
                    proxy: str = doc['proxy']
                    pattern = re.compile(
                        r'(.+\.)?{}$'.format(re.escape(proxy.lstrip('.'))),
                        flags=re.IGNORECASE
                    )
                    proxies[scheme].append(pattern)

        if 'no' in proxies and '*' in proxies['no']:
            proxies.update({'no': '*'})

        return dict(proxies)

    @property
    def proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        return self._proxies

    @proxies.setter
    def proxies(self, proxies: Dict[str, Union[str, List[Tuple[bytes, str]]]]):
        self._proxies = proxies

        self.proxies_iter = dict()
        for key, value in proxies.items():
            if key != 'no':
                self.proxies_iter.update({key: iter(value)})

    def _prepare_conn_args(self) -> Dict:
        return dict(filter(
            lambda x: x[0] not in self.not_mongoclient_parameters,
            self.mongodb_settings.items()
        ))

    def _get_mongodb_settings(self) -> Dict:
        if (
                self.settings.getpriority('HTTPPROXY_MONGODB_AUTHSOURCE') ==
                SETTINGS_PRIORITIES['default']
        ):
            with unfreeze_settings(self.settings) as settings:
                settings.set(
                    'HTTPPROXY_MONGODB_AUTHSOURCE',
                    self.settings.get('HTTPPROXY_MONGODB_DATABASE')
                )

        return dict(starmap(
            lambda k, v: (k.replace('HTTPPROXY_MONGODB_', '').lower(), v),
            filter(lambda x: x[0].startswith('HTTPPROXY_MONGODB_'),
                   self.settings.items())
        ))
