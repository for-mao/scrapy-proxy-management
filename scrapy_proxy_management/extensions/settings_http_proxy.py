import re
from itertools import cycle
from itertools import starmap
from typing import Dict
from typing import Generator
from typing import Iterator
from typing import List
from typing import Tuple
from urllib.parse import splitport

from scrapy.settings import Settings
from scrapy.spiders import Spider

from . import BaseProxyStorage


class SettingsProxyStorage(BaseProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str, mw):
        super().__init__(settings, auth_encoding, mw)

        self._proxies: Dict[str, List[Tuple[bytes, str]]] = None
        self.proxies: Dict[str, Iterator[Tuple[bytes, str], None, None]] = None

    def open_spider(self, spider: Spider):
        self._load_proxies()
        self.log.info('Proxy storage by settings is opening.')

    def close_spider(self, spider: Spider):
        self.log.info('Proxy storage by settings is closed')

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        """Test if proxies should not be used for a particular host.

        Checks the proxy dict for the value of no_proxy, which should
        be a list of comma separated DNS suffixes, or '*' for all hosts.

        """
        if proxies is None:
            proxies = self._proxies

        # don't bypass, if no_proxy isn't specified
        try:
            no_proxy: List = proxies['no']
        except KeyError:
            return False

        # '*' is special case for always bypass
        if '*' in no_proxy:
            return True

        # strip port off host
        host_only, port = splitport(host)

        for pattern in no_proxy:
            if any(map(lambda x: pattern.match(x), [host_only, host])):
                return True

        # otherwise, don't bypass
        return False

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        return next(self.proxies[scheme])

    def _get_proxies(self) -> Dict:
        _proxies = {}

        for type_, proxies in self.settings['HTTPPROXY_PROXIES'].items():
            if type_ != 'no':
                _proxies.update({
                    type_: list(map(
                        lambda x: self._get_proxy(x, type_),
                        proxies
                    ))
                })
            elif type_ == 'no':
                _proxies.update({
                    type_: list(map(
                        lambda x: x if x == '*' else re.compile(
                            r'(.+\.)?{}$'.format(re.escape(x.lstrip('.'))),
                            flags=re.IGNORECASE
                        ),
                        proxies
                    ))
                })

        return _proxies

    def _load_proxies(self):
        self._proxies: Dict[str, List[Tuple[bytes, str]]] = self._get_proxies()
        self.proxies: Dict[
            str, Generator[Tuple[bytes, str], None, None]
        ] = dict(starmap(lambda k, v: (k, cycle(v)), self._proxies.items()))
