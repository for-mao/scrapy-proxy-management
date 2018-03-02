import logging

from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import SETTINGS_PRIORITIES
from scrapy.settings import Settings
from scrapy.signals import spider_closed
from scrapy.signals import spider_opened
from scrapy.spiders import Spider
from scrapy.statscollectors import StatsCollector
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.misc import load_object

from . import unfreeze_settings
from ..extensions.environment_http_proxy import ProxyStorage
from ..settings import default_settings
from ..signals import proxy_invalidated

logger = logging.getLogger(__name__)


class HttpProxyMiddleware(object):

    def __init__(self, crawler: Crawler, auth_encoding: str = 'latin-1'):
        self.crawler: Crawler = crawler
        self.settings: Settings = crawler.settings
        self.auth_encoding: str = auth_encoding
        self.stats: StatsCollector = crawler.stats

        with unfreeze_settings(self.settings) as settings:
            settings.setmodule(
                module=default_settings,
                priority=SETTINGS_PRIORITIES['default']
            )

        self.storage: ProxyStorage = load_object(
            self.settings['HTTPPROXY_STORAGE']
        )(settings=self.settings, auth_encoding=self.auth_encoding)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        if not crawler.settings.getbool('HTTPPROXY_ENABLED'):
            raise NotConfigured

        obj = cls(crawler, crawler.settings.get('HTTPPROXY_AUTH_ENCODING'))

        crawler.signals.connect(obj.spider_opened, signal=spider_opened)
        crawler.signals.connect(obj.spider_close, signal=spider_closed)
        crawler.signals.connect(obj.proxy_invalidated, signal=proxy_invalidated)

        return obj

    def spider_opened(self, spider: Spider):
        self.storage.open_spider(spider)

    def spider_close(self, spider: Spider):
        self.storage.close_spider(spider)

    def proxy_invalidated(self, request: Request, response: Response,
                          spider: Spider):
        self.storage.invalidate_proxy(
            request=request, response=response, spider=spider
        )
        self.stats.inc_value('proxy_invalidated', spider=spider)

    def process_request(self, request: Request, spider: Spider):
        # ignore if proxy is already set
        if 'proxy' in request.meta:
            if request.meta['proxy'] is None:
                return
            # extract credentials if present
            credentials, proxy_url = self.storage._get_proxy(
                request.meta['proxy'], ''
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
                self.storage.proxy_bypass(parsed.hostname)
        )):
            return

        if scheme in self.storage.proxies:
            self._set_proxy(request, scheme)

    def _set_proxy(self, request: Request, scheme: str):
        credentials, proxy = self.storage.retrieve_proxy(scheme)
        request.meta['proxy'] = proxy
        if credentials:
            request.headers['Proxy-Authorization'] = b'Basic ' + credentials
