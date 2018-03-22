import logging
import re
from itertools import cycle
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from urllib.request import getproxies

from scrapy.crawler import Crawler

from . import BaseStorage
from ..utils import get_proxy

logger = logging.getLogger(__name__)


class EnvironmentStorage(BaseStorage):
    def __init__(self, crawler: Crawler, mw, auth_encoding: str):
        super(EnvironmentStorage, self).__init__(crawler, mw, auth_encoding)

    def load_proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        proxies = {}

        for scheme, proxy in getproxies().items():
            if scheme != 'no':
                proxies.update({
                    scheme: get_proxy(self.auth_encoding, proxy, scheme)
                })
            elif scheme == 'no':
                if proxy == '*':
                    proxies.update({scheme: proxy})
                else:
                    patterns = list(map(
                        lambda x: re.compile(
                            r'(.+\.)?{}$'.format(re.escape(x.lstrip('.'))),
                            flags=re.IGNORECASE
                        ),
                        proxy.split(',')
                    ))
                    proxies.update({scheme: patterns})

        return proxies

    @property
    def proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        return self._proxies

    @proxies.setter
    def proxies(self, proxies: Dict[str, Union[str, List[Tuple[bytes, str]]]]):
        self._proxies = proxies

        self.proxies_iter = dict()
        for key, value in proxies.items():
            if key != 'no':
                self.proxies_iter.update({key: cycle([value])})
