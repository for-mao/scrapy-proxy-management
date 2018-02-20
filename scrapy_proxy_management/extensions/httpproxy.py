import base64
import logging
from itertools import cycle
from itertools import starmap
from typing import Dict
from typing import Generator
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlunparse
from urllib.request import _parse_proxy
from urllib.request import getproxies

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

    def invalidate_proxy(self, spider: Spider):
        raise NotImplementedError

    def retrieve_proxy(self, scheme: str) -> Generator[
        Tuple[bytes, str], None, None
    ]:
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


class EnvironmentProxyStorage(ProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str):
        super(EnvironmentProxyStorage, self).__init__(settings, auth_encoding)
        self.proxies: Dict[
            str, Generator[Tuple[bytes, str], None, None]
        ] = dict(starmap(
            lambda type_, url: (type_, cycle([self._get_proxy(url, type_)])),
            getproxies().items()
        ))

    def open_spider(self, spider: Spider):
        self.log.info(
            'Proxy storage by environment variables is opening.'
        )

    def close_spider(self, spider: Spider):
        self.log.info('Proxy storage by environment variables is closed')

    def invalidate_proxy(self, spider: Spider):
        raise NotImplementedError

    def retrieve_proxy(self, scheme: str) -> Generator[
        Tuple[bytes, str], None, None
    ]:
        yield from self.proxies[scheme]
