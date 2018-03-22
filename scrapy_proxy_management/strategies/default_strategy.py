import logging
import re

from scrapy.spiders import Spider

from . import BaseStrategy

logger = logging.getLogger(__name__)

pattern_credential = re.compile(rb'^Basic\s(?P<credential>.*)')


class DefaultStrategy(BaseStrategy):
    supported_storage = (
        'scrapy_proxy_management.storages.environment_storage.EnvironmentStorage',
        'scrapy_proxy_management.storages.settings_storage.SettingsStorage'
    )

    def retrieve_proxy(self, scheme: str, spider: Spider):
        return next(self.storage.proxies_iter[scheme])
