import logging
from abc import ABCMeta
from abc import abstractmethod

from scrapy.settings import Settings

from .. import BaseProxyStorage


class BaseProxyManagementStrategy(metaclass=ABCMeta):
    def __init__(self, settings: Settings, proxy_storage: BaseProxyStorage):
        self.settings = settings
        self.proxy_storage = proxy_storage
        self.log = logging.getLogger(
            '{}.{}'.format(self.__module__, self.__class__.__name__)
        )

    @classmethod
    def from_crawler(cls, settings: Settings, proxy_storage: BaseProxyStorage):
        obj = cls(settings, proxy_storage)
        return obj

    @abstractmethod
    def open_spider(self):
        pass

    @abstractmethod
    def close_spider(self):
        pass

    @abstractmethod
    def invalidate_proxy(
            self, proxy: str, scheme: str, credential: bytes = None
    ):
        pass

    @abstractmethod
    def reload_proxies(self):
        pass
