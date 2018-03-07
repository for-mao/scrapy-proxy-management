import base64
import logging
from abc import ABCMeta
from abc import abstractmethod
from functools import lru_cache
from typing import Dict
from typing import Iterator
from typing import List
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlunparse
from urllib.request import _parse_proxy

from scrapy.crawler import Crawler
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.spiders import Spider


def basic_auth_header(
        username: str, password: str, auth_encoding: str
) -> bytes:
    return base64.b64encode(bytes(
        '{}:{}'.format(unquote(username), unquote(password)),
        encoding=auth_encoding
    )).strip()


class BaseProxyStorage(metaclass=ABCMeta):
    def __init__(self, settings: Settings, auth_encoding: str, mw):
        self.auth_encoding = auth_encoding
        self.settings = settings
        self.mw = mw
        self.log = logging.getLogger(
            '{}.{}'.format(self.__module__, self.__class__.__name__)
        )
        self._proxy: Dict[str, List[Tuple[bytes, str]]] = None
        self.proxies: Dict[str, Iterator[Tuple[bytes, str], None, None]] = None

    @classmethod
    def from_crawler(cls, crawler: Crawler, auth_encoding: str, mw):
        # hack the decorator lru_cache, to customize the maxsize of lru_cache to
        # cache by the number in the settings
        cls.proxy_bypass = lru_cache(
            maxsize=crawler.settings['HTTPPROXY_PROXY_BYPASS_LRU_CACHE']
        )(cls.proxy_bypass)

        obj = cls(crawler.settings, auth_encoding, mw)

        return obj

    @abstractmethod
    def open_spider(self, spider: Spider):
        pass

    @abstractmethod
    def close_spider(self, spider: Spider):
        pass

    def invalidate_proxy(self, spider: Spider, request: Request, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def proxy_bypass(self, host: str, proxies=None) -> bool:
        pass

    @abstractmethod
    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        pass

    def _get_proxy(self, url: str, orig_type: str) -> Tuple[bytes, str]:
        proxy_type, user, password, host_port = _parse_proxy(url)
        proxy_url: str = urlunparse((
            proxy_type or orig_type, host_port, '', '', '', ''
        ))
        credentials = (
            basic_auth_header(user, password, self.auth_encoding)
            if user else None
        )
        return credentials, proxy_url

    @abstractmethod
    def _load_proxies(self):
        pass
