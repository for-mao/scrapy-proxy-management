from collections import defaultdict
from copy import deepcopy
from itertools import starmap
from urllib.parse import urlparse

from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.spiders import Spider

from . import BaseProxyManagementStrategy
from ...extensions import BaseProxyStorage


class DefaultProxyManagementStrategy(BaseProxyManagementStrategy):
    def __init__(self, settings: Settings, proxy_storage: BaseProxyStorage):
        super().__init__(settings, proxy_storage)

    def open_spider(self):
        self.log.info(
            '%s is used in %s',
            self.__class__.__name__,
            self.proxy_storage.__class__.__name__
        )
        self.proxy_storage._load_proxies()

    def close_spider(self):
        pass

    def invalidate_proxy(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None, **kwargs
    ):
        proxy, scheme, credential = None, None, None
        if request:
            proxy = request.meta['proxy']
            scheme = urlparse(request.url).scheme
            credential = request.headers.get('Proxy-Authorization')
        elif response:
            proxy = response.request.meta['proxy']
            scheme = urlparse(response.request.url).scheme
            credential = response.request.headers.get('Proxy-Authorization')

        if (
                (scheme, credential, proxy) not in
                self.proxy_storage.proxies_invalidated
        ):
            self.proxy_storage.proxies_invalidated.add(
                (scheme, credential, proxy)
            )
            if isinstance(exception, Exception):
                self.proxy_storage.mw.stats.inc_value(
                    'proxy/{}/invalidated/{}'.format(
                        scheme, exception.__class__.__name__
                    ),
                    spider=spider
                )
            elif isinstance(exception, str):
                self.proxy_storage.mw.stats.inc_value(
                    'proxy/{}/invalidated/{}'.format(scheme, exception),
                    spider=spider
                )
            else:
                self.proxy_storage.mw.stats.inc_value(
                    'proxy/{}/invalidated/others_reasons'.format(scheme),
                    spider=spider
                )

    def reload_proxies(self):
        self.proxy_storage.proxy_bypass.cache_clear()

        _proxies = deepcopy(self.proxy_storage._proxies)
        self.proxy_storage._proxies = defaultdict(list)

        for k, v in filter(lambda x: x[0] != 'no', _proxies.items()):
            for _proxy in filter(
                    lambda x: (k,
                               *x) not in self.proxy_storage.proxies_invalidated,
                    v
            ):
                self.proxy_storage._proxies[k].append(_proxy)

        if self.proxy_storage._proxies:
            self.proxy_storage.proxies = dict(starmap(
                lambda k, v: (k, iter(v)), self.proxy_storage._proxies.items()
            ))
        else:
            self.proxy_storage.mw.crawler.stop()
