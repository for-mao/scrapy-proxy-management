import base64
import logging
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlunparse
from urllib.request import _parse_proxy

from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.spiders import Spider


class ProxyStorage(object):
    def __init__(self, settings: Settings, auth_encoding: str):
        self.settings = settings
        self.auth_encoding = auth_encoding
        self.log = logging.getLogger(
            '{}.{}'.format(self.__module__, self.__class__.__name__)
        )
        self.proxies = None

    def open_spider(self, spider: Spider):
        raise NotImplementedError

    def close_spider(self, spider: Spider):
        raise NotImplementedError

    def invalidate_proxy(
            self, request: Request, response: Response, spider: Spider
    ):
        raise NotImplementedError

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        raise NotImplementedError

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        raise NotImplementedError

    def _get_proxy(self, url: str, orig_type: str) -> Tuple[bytes, str]:
        proxy_type, user, password, host_port = _parse_proxy(url)
        proxy_url: str = urlunparse((
            proxy_type or orig_type, host_port, '', '', '', ''
        ))
        credentials = self._basic_auth_header(user, password) if user else None
        return credentials, proxy_url

    def _basic_auth_header(self, username: str, password: str) -> bytes:
        return base64.b64encode(bytes(
            '{}:{}'.format(unquote(username), unquote(password)),
            encoding=self.auth_encoding
        )).strip()
