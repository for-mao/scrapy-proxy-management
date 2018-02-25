from itertools import starmap
from typing import Dict
from typing import Tuple
from urllib.request import getproxies

from scrapy.settings import Settings
from scrapy.spiders import Spider

from . import ProxyStorage


class EnvironmentProxyStorage(ProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str):
        super(EnvironmentProxyStorage, self).__init__(settings, auth_encoding)
        self.proxies: Dict[str, Tuple[bytes, str]] = dict(starmap(
            lambda type_, url: (type_, self._get_proxy(url, type_)),
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

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        return self.proxies[scheme]
