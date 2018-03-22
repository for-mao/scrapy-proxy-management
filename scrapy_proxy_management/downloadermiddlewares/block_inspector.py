import logging
import pprint
from typing import List
from typing import Tuple

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
from scrapy.utils.misc import load_object
from twisted.internet.defer import inlineCallbacks

from ..settings import default_settings
from ..utils import unfreeze_settings

logger = logging.getLogger(__name__)


class BlockInspectorMiddleware(object):
    def __init__(self, crawler: Crawler):
        self.crawler: Crawler = crawler
        self.settings: Settings = crawler.settings
        self.signals: SignalManager = crawler.signals
        self.stats: StatsCollector = crawler.stats

        with unfreeze_settings(self.settings) as settings:
            settings.setmodule(
                module=default_settings,
                priority=SETTINGS_PRIORITIES['default']
            )

        self.SIGNALS = list(map(
            lambda x: load_object(x),
            crawler.settings.get('HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS')
        ))

        self.SIGNALS_DEFERRED = list(map(
            lambda x: load_object(x),
            crawler.settings.get(
                'HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS_DEFERRED')
        ))

        self.PROXY_INVALIDATED_EXCEPTIONS = tuple(map(
            lambda x: load_object(x),
            self.settings.getlist('HTTPPROXY_PROXY_INVALIDATED_EXCEPTIONS')
        ))

    def spider_opened(self):
        logger.info('%s is opened', self.__class__.__name__)
        logger.info(
            '%s is used to inspect block',
            self.settings.get('HTTPPROXY_PROXY_DM_BLOCK_INSPECTOR')
        )
        logger.info(
            'The following status codes will be reported as proxy invalidated:'
            '\n%s', pprint.pformat(self.settings.getlist(
                'HTTPPROXY_PROXY_INVALIDATED_STATUS_CODES'
            ))
        )
        logger.info(
            'The following exceptions will be reported as proxy invalidated:'
            '\n%s', pprint.pformat(
                self.settings.get('HTTPPROXY_PROXY_INVALIDATED_EXCEPTIONS')
            )
        )

        if self.settings.get('HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS'):
            logger.info(
                'The following signals will be sent when block is inspected:'
                '\n%s', pprint.pformat(self.settings.get(
                    'HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS'
                ))
            )
        if self.settings.get(
                'HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS_DEFERRED'
        ):
            logger.info(
                'The following signals deferred will be sent when block is '
                'inspected:\n%s', pprint.pformat(self.settings.get(
                    'HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS_DEFERRED'
                ))
            )

    def spider_closed(self):
        pass

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        if not crawler.settings.get('HTTPPROXY_PROXY_DM_BLOCK_INSPECTOR'):
            raise NotConfigured

        cls.inspect_block = load_object(
            crawler.settings.get('HTTPPROXY_PROXY_DM_BLOCK_INSPECTOR')
        )

        cls.recycle_request = load_object(
            crawler.settings.get('HTTPPROXY_DM_RECYCLE_REQUEST')
        )

        obj = cls(crawler)

        crawler.signals.connect(obj.spider_opened, signal=spider_opened)
        crawler.signals.connect(obj.spider_closed, signal=spider_closed)

        return obj

    @inlineCallbacks
    def process_response(
            self, request: Request, response: Response, spider: Spider
    ):
        try:
            self.inspect_block(
                request=request, response=response, spider=spider
            )
        except self.PROXY_INVALIDATED_EXCEPTIONS as exc:
            self.stats.inc_value('block_inspector/block', spider=spider)
            results, results_deferred = yield self.send_signals(
                request=request, response=response, exception=exc, spider=spider
            )
            return self.recycle_request(request, spider)
        else:
            return response

    @inlineCallbacks
    def process_exception(
            self, request: Request, exception: Exception, spider: Spider
    ):
        if isinstance(exception, self.PROXY_INVALIDATED_EXCEPTIONS):
            self.stats.inc_value('block_inspector/block', spider=spider)

            results, results_deferred = yield self.send_signals(
                request=request, exception=exception, spider=spider
            )

            return self.recycle_request(request, spider)

    @inlineCallbacks
    def send_signals(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None
    ) -> Tuple[List, List]:
        results = list()
        results_deferred = list()

        for signal in self.SIGNALS:
            results.append(self.signals.send_catch_log(
                signal=signal, request=request, response=response,
                exception=exception, spider=spider
            ))
        for signal in self.SIGNALS_DEFERRED:
            _result = yield self.signals.send_catch_log_deferred(
                signal=signal, request=request, response=response,
                exception=exception, spider=spider
            )
            results_deferred.append(_result)

        return results, results_deferred
