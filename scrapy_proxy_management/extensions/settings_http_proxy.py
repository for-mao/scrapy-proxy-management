import re
from itertools import cycle
from itertools import starmap
from typing import Dict
from typing import Generator
from typing import List
from typing import Tuple
from urllib.parse import splitport

from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.spiders import Spider

from . import ProxyStorage


class SettingsProxyStorage(ProxyStorage):
    def __init__(self, settings: Settings, auth_encoding: str):
        super(SettingsProxyStorage, self).__init__(settings, auth_encoding)

        self._proxies: Dict[str, List[Tuple[bytes, str]]] = self._get_proxies()

        self.proxies: Dict[
            str, Generator[Tuple[bytes, str], None, None]
        ] = dict(starmap(lambda k, v: (k, cycle(v)), self._proxies.items()))

    def open_spider(self, spider: Spider):
        self.log.info('Proxy storage by settings is opening.')

    def close_spider(self, spider: Spider):
        self.log.info('Proxy storage by settings is closed')

    def invalidate_proxy(
            self, request: Request, response: Response, spider: Spider
    ):
        raise NotImplementedError

    def retrieve_proxy(self, scheme: str) -> Tuple[bytes, str]:
        return next(self._retrieve_proxy(scheme))

    def _retrieve_proxy(
            self, scheme: str
    ) -> Generator[Tuple[bytes, str], None, None]:
        yield from self.proxies[scheme]

    def _get_proxies(self):
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

    def proxy_bypass(self, host: str, proxies=None) -> bool:
        return self._proxy_bypass(
            host=host,
            proxies=proxies if proxies else None
        )

    def _proxy_bypass(self, host: str, proxies=None) -> bool:
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
        else:
            # '*' is special case for always bypass
            if '*' in no_proxy:
                return True
            else:
                # strip port off host
                host_only, port = splitport(host)

                for pattern in no_proxy:
                    if any(map(lambda x: pattern.match(x), [host_only, host])):
                        return True
                else:
                    # otherwise, don't bypass
                    return False
