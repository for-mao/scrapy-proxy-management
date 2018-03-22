import logging

from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import SETTINGS_PRIORITIES
from scrapy.settings import Settings
from scrapy.signalmanager import SignalManager
from scrapy.signals import spider_closed
from scrapy.signals import spider_opened
from scrapy.spiders import Spider
from scrapy.statscollectors import StatsCollector
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.misc import load_object

from ..exceptions import ProxyExhaustedException
from ..settings import default_settings
from ..signals import proxy_invalidated
from ..storages.environment_storage import BaseStorage
from ..strategies import BaseStrategy
from ..utils import get_proxy
from ..utils import unfreeze_settings

logger = logging.getLogger(__name__)


class HttpProxyMiddleware(object):
    def __init__(self, crawler: Crawler, auth_encoding: str = 'latin-1'):
        self.auth_encoding: str = auth_encoding
        self.crawler: Crawler = crawler
        self.settings: Settings = crawler.settings
        self.signals: SignalManager = crawler.signals
        self.stats: StatsCollector = crawler.stats

        with unfreeze_settings(self.settings) as settings:
            settings.setmodule(
                module=default_settings,
                priority=SETTINGS_PRIORITIES['default']
            )

        cls_storage = load_object(self.settings['HTTPPROXY_STORAGE'])
        self.storage: BaseStorage = cls_storage.from_crawler(
            crawler=self.crawler, mw=self, auth_encoding=self.auth_encoding
        )

        cls_strategy = load_object(self.settings['HTTPPROXY_STRATEGY'])
        self.strategy: BaseStrategy = cls_strategy.from_crawler(
            crawler=self.crawler, mw=self, storage=self.storage
        )

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        if any((not crawler.settings.get('HTTPPROXY_ENABLED'),
                not crawler.settings.get('HTTPPROXY_STORAGE'),
                not crawler.settings.get('HTTPPROXY_STRATEGY'))):
            raise NotConfigured

        obj = cls(crawler, crawler.settings.get('HTTPPROXY_AUTH_ENCODING'))

        crawler.signals.connect(obj.open_spider, signal=spider_opened)
        crawler.signals.connect(obj.close_spider, signal=spider_closed)
        crawler.signals.connect(obj.invalidate_proxy, signal=proxy_invalidated)

        return obj

    def open_spider(self, spider: Spider):
        self.strategy.open_spider(spider)

    def close_spider(self, spider: Spider):
        self.strategy.close_spider(spider)

    def process_request(self, request: Request, spider: Spider):
        # ignore if proxy is already set
        if 'proxy' in request.meta:
            if request.meta['proxy'] is None:
                return
            # extract credentials if present
            credentials, proxy_url = get_proxy(
                self.auth_encoding, request.meta['proxy'], ''
            )
            request.meta['proxy'] = proxy_url
            if credentials and not request.headers.get('Proxy-Authorization'):
                request.headers['Proxy-Authorization'] = b'Basic ' + credentials
            return
        elif not self.storage.proxies:
            return

        parsed = urlparse_cached(request)
        scheme = parsed.scheme

        # 'no_proxy' is only supported by http schemes
        if all((
                scheme in ('http', 'https'),
                self.strategy.proxy_bypass(host=parsed.hostname, spider=spider)
        )):
            return

        if scheme in self.storage.proxies:
            self._set_proxy(request, scheme, spider)
        else:
            return

    def invalidate_proxy(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None, **kwargs
    ):
        self.strategy.invalidate_proxy(
            request, response, exception, spider, **kwargs
        )
        req = request if request else response.request
        logger.debug(
            'Proxy %s is invalidated because of %s',
            req.meta['proxy'], str(exception)
        )
        self.strategy.invalidate_proxy(
            request, response, exception, spider, **kwargs
        )

    def _set_proxy(self, request: Request, scheme: str, spider: Spider):
        try:
            credentials, proxy = self.strategy.retrieve_proxy(scheme, spider)
        except ProxyExhaustedException as exc:
            logger.warning('%s proxy is exhausted', scheme)
            self.strategy.proxy_exhausted(
                request=request, scheme=scheme, spider=spider
            )
        else:
            request.meta['proxy'] = proxy
            if credentials:
                request.headers['Proxy-Authorization'] = b'Basic ' + credentials
