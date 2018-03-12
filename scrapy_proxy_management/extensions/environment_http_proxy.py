import logging
from itertools import starmap
from typing import Dict
from typing import Tuple
from urllib.request import getproxies
from urllib.request import proxy_bypass

from scrapy.settings import Settings
from scrapy.spiders import Spider

from . import BaseProxyStorage

logger = logging.getLogger(__name__)


class EnvironmentProxyStorage(BaseProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str, mw):
        super().__init__(settings, auth_encoding, mw)

        self.proxies: Dict[str, Tuple[bytes, str]] = None

    def open_spider(self, spider: Spider):
        self._load_proxies()

        logger.info(
            'Proxy storage by environment variables is opening.'
        )

    def close_spider(self, spider: Spider):
        logger.info('Proxy storage by environment variables is closed')

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        return proxy_bypass(host=host, proxies=proxies)

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        return self.proxies[scheme]

    def _load_proxies(self):
        self.proxies: Dict[str, Tuple[bytes, str]] = dict(starmap(
            lambda type_, url: (
                type_, self._get_proxy(url, type_)
            ),
            getproxies().items()
        ))
