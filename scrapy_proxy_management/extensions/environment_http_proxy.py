from itertools import starmap
from typing import Dict
from typing import Tuple
from urllib.request import getproxies
from urllib.request import proxy_bypass

from scrapy.http import Request
from scrapy.http import Response
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

    def invalidate_proxy(
            self, request: Request, response: Response, spider: Spider
    ):
        raise NotImplementedError

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        return self.proxies[scheme]

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        return proxy_bypass(host=host, proxies=proxies)
