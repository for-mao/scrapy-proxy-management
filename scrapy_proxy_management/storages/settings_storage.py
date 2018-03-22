import logging
import re
from itertools import cycle
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from scrapy.crawler import Crawler

from . import BaseStorage
from ..utils import get_proxy

logger = logging.getLogger(__name__)


class SettingsStorage(BaseStorage):
    def __init__(self, crawler: Crawler, auth_encoding: str, mw):
        super().__init__(crawler, auth_encoding, mw)

    def load_proxies(self) -> Dict[str, Union[str, List[Tuple[bytes, str]]]]:
        proxies = {}

        for scheme, proxies_ in self.settings['HTTPPROXY_PROXIES'].items():
            if scheme != 'no':
                proxies.update({
                    scheme: list(map(
                        lambda x: get_proxy(self.auth_encoding, x, scheme),
                        proxies_
                    ))
                })
            elif scheme == 'no':
                if isinstance(proxies_, list) and '*' in proxies_:
                    proxies.update({scheme: '*'})
                elif isinstance(proxies_, str) and '*' == proxies_:
                    proxies.update({scheme: proxies_})
                else:
                    patterns = list(map(
                        lambda x: re.compile(
                            r'(.+\.)?{}$'.format(re.escape(x.lstrip('.'))),
                            flags=re.IGNORECASE
                        ),
                        proxies_
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
                self.proxies_iter.update({key: cycle(value)})
