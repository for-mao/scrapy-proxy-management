import logging
from abc import ABCMeta
from abc import abstractmethod
from typing import Dict
from typing import Iterator
from typing import List
from typing import Sequence
from typing import Set
from typing import Tuple
from typing import Union

from scrapy.crawler import Crawler
from scrapy.settings import Settings
from scrapy.signalmanager import SignalManager
from scrapy.spiders import Spider
from scrapy.statscollectors import StatsCollector

logger = logging.getLogger(__name__)


class BaseStorage(metaclass=ABCMeta):
    def __init__(self, crawler: Crawler, mw, auth_encoding: str):
        self.auth_encoding: str = auth_encoding
        self.crawler: Crawler = crawler
        self.mw = mw
        self.settings: Settings = crawler.settings
        self.signals: SignalManager = mw.signals
        self.stats: StatsCollector = mw.stats

        self._proxies: Dict[str, Union[str, List[Tuple[bytes, str]]]] = dict()
        self.proxies_iter: Dict[
            str, Union[str, Iterator[Tuple[bytes, str]]]
        ] = dict()
        self.proxies_invalidated: Set[Tuple[str, bytes, str]] = set()

    @classmethod
    def from_crawler(cls, crawler: Crawler, mw, auth_encoding: str):
        obj = cls(crawler, mw, auth_encoding)
        return obj

    def open_spider(self, spider: Spider):
        logger.info('Proxy storage %s is opened', self.__class__.__name__)

        self.proxies = self.load_proxies()

        for scheme, proxies in self.proxies.items():
            logger.info('Loaded %s %s proxies', len(proxies), scheme)
            self.stats.set_value(
                'proxy/{scheme}'.format(scheme=scheme),
                len(proxies) if isinstance(proxies, Sequence) else 1
            )

    def close_spider(self, spider: Spider):
        logger.info('Proxy storage %s is closed', self.__class__.__name__)

    @abstractmethod
    def load_proxies(self) -> Dict[str, Tuple[bytes, str]]:
        pass

    @property
    @abstractmethod
    def proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        return self._proxies

    @proxies.setter
    @abstractmethod
    def proxies(self, proxies: Dict[str, Union[str, List[Tuple[bytes, str]]]]):
        self._proxies = proxies
