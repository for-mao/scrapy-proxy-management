import logging
from abc import ABCMeta
from abc import abstractmethod
from functools import lru_cache
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from urllib.parse import splitport

from scrapy.crawler import Crawler
from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.signalmanager import SignalManager
from scrapy.spiders import Spider
from scrapy.statscollectors import StatsCollector
from scrapy.utils.misc import load_object

from ..exceptions import StorageNotSupportException
from ..storages import BaseStorage

logger = logging.getLogger(__name__)


class BaseStrategy(metaclass=ABCMeta):
    supported_storage = ()

    def __init__(self, crawler: Crawler, mw, storage: BaseStorage):
        self.crawler: Crawler = crawler
        self.mw = mw
        self.settings: Settings = crawler.settings
        self.stats: StatsCollector = crawler.stats
        self.signals: SignalManager = crawler.signals

        self.storage: BaseStorage = storage

    @classmethod
    def from_crawler(cls, crawler: Crawler, mw, storage: BaseStorage):
        supported_storage = tuple(map(
            lambda x: load_object(x), cls.supported_storage
        ))
        if not isinstance(storage, supported_storage):
            logger.critical(
                'The storage %s is not supported by %s',
                type(storage), cls.__name__
            )
            raise StorageNotSupportException

        # hack the decorator lru_cache, to customize the maxsize of lru_cache to
        # cache by the number in the settings
        cls.proxy_bypass = lru_cache(
            maxsize=crawler.settings['HTTPPROXY_PROXY_BYPASS_LRU_CACHE']
        )(cls.proxy_bypass)

        obj = cls(crawler, mw, storage)
        return obj

    def open_spider(self, spider: Spider):
        logger.info('Strategy %s is opened', self.__class__.__name__)
        self.storage.open_spider(spider)

    def close_spider(self, spider: Spider):
        logger.info('Strategy %s is closed', self.__class__.__name__)
        self.storage.close_spider(spider)

    def invalidate_proxy(
            self, request: Request = None, response: Response = None,
            exception: Exception = None, spider: Spider = None, **kwargs
    ):
        raise NotImplementedError

    def proxy_exhausted(self, request: Request, scheme: str, spider: Spider):
        raise NotImplementedError

    def proxy_bypass(
            self, host: str,
            spider: Spider = None,
            proxies: Dict[str, Union[str, List[Tuple[bytes, str]]]] = None
    ):
        """Test if proxies should not be used for a particular host.

        Checks the proxy dict for the value of no_proxy, which should
        be a list of comma separated DNS suffixes, or '*' for all hosts.

        """
        if proxies is None:
            proxies = self.storage.proxies

        # don't bypass, if no_proxy isn't specified
        try:
            no_proxy: List = proxies['no']
        except KeyError:
            return False

        # '*' is special case for always bypass
        if isinstance(no_proxy, str) and '*' == no_proxy:
            return True

        # strip port off host
        host_only, port = splitport(host)

        for pattern in no_proxy:
            if any(map(lambda x: pattern.match(x), [host_only, host])):
                return True

        # otherwise, don't bypass
        return False

    @abstractmethod
    def retrieve_proxy(self, scheme: str, spider: Spider):
        pass
