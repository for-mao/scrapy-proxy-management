from collections import defaultdict
from copy import deepcopy
from itertools import starmap

from scrapy.settings import Settings

from . import BaseProxyManagementStrategy
from ...extensions import BaseProxyStorage


class DefaultProxyManagementStrategy(BaseProxyManagementStrategy):
    def __init__(self, settings: Settings, proxy_storage: BaseProxyStorage):
        super().__init__(settings, proxy_storage)

    def open_spider(self):
        self.proxy_storage._load_proxies()

    def close_spider(self):
        pass

    def invalidate_proxy(
            self, proxy: str, scheme: str, credential: bytes = None
    ):
        self.proxy_storage.invalidate_proxies.add((scheme, credential, proxy))

    def reload_proxies(self):
        self.proxy_storage.proxy_bypass.cache_clear()

        _proxies = deepcopy(self.proxy_storage._proxies)
        self.proxy_storage._proxies = defaultdict(list)

        for k, v in filter(lambda x: x[0] != 'no', _proxies.items()):
            for _proxy in filter(
                    lambda x: (k, *x) not in self.proxy_storage.invalidate_proxies,
                    v
            ):
                self.proxy_storage._proxies[k].append(_proxy)

        if self.proxy_storage._proxies:
            self.proxy_storage.proxies = dict(starmap(
                lambda k, v: (k, iter(v)), self.proxy_storage._proxies.items()
            ))
        else:
            self.proxy_storage.mw.crawler.stop()
