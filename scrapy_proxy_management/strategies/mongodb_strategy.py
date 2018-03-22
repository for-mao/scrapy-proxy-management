import logging
import re
from collections import defaultdict
from urllib.parse import urlparse

from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request
from scrapy.http import Response
from scrapy.spiders import Spider

from . import BaseStrategy
from ..exceptions import ProxyExhaustedException

logger = logging.getLogger(__name__)

pattern_credential = re.compile(rb'^Basic\s(?P<credential>.*)')


class MongoDBStrategy(BaseStrategy):
    supported_storage = (
        'scrapy_proxy_management.storages.mongodb_storage.MongoDBSyncStorage',
    )

    def invalidate_proxy(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None, **kwargs
    ):
        req = request if request else response.request

        scheme: str = urlparse(req.url).scheme
        if 'Proxy-Authorization' in req.headers:
            credential: bytes = pattern_credential.match(
                req.headers['Proxy-Authorization']
            ).group('credential')
        else:
            credential = None
        proxy: str = req.meta['proxy']

        self.storage.proxies_invalidated.add((scheme, credential, proxy))

    def proxy_exhausted(self, request: Request, scheme: str, spider: Spider):
        logger.warning(
            'Proxy scheme %s is exhausted, ignore current request and stop the '
            'spider now',
            scheme
        )
        self.crawler.engine.close_spider(
            spider, reason='Proxy scheme {} is exhausted'.format(scheme)
        )
        raise IgnoreRequest

    def reload_proxies(self, spider: Spider):
        orig_proxies = self.storage.load_proxies()
        proxies = defaultdict(list)
        if 'no' in orig_proxies:
            proxies.update({'no': orig_proxies.pop('no')})

        for key, value in orig_proxies.items():
            for value_ in value:
                if (key, *value_) not in self.storage.proxies_invalidated:
                    proxies[key].append(value_)

        return dict(proxies)

    def retrieve_proxy(self, scheme: str, spider: Spider):
        try:
            return next(self.storage.proxies_iter[scheme])
        except StopIteration as exc:
            self.storage.proxies = self.storage.load_proxies()
            if scheme in self.storage.proxies:
                return next(self.storage.proxies_iter[scheme])
            else:
                raise ProxyExhaustedException from exc
