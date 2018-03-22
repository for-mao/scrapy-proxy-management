import base64
from contextlib import contextmanager
from copy import copy
from typing import Any
from typing import Generator
from typing import Tuple
from urllib.parse import unquote
from urllib.parse import urlunparse
from urllib.request import _parse_proxy

from scrapy.http import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.spiders import Spider

from .inspect_google_recaptcha import inspect_google_recaptcha


@contextmanager
def unfreeze_settings(settings: Settings):
    original_status = settings.frozen
    settings.frozen = False
    try:
        yield settings
    finally:
        settings.frozen = original_status


def basic_auth_header(
        username: str, password: str, auth_encoding: str
) -> bytes:
    return base64.b64encode(bytes(
        '{}:{}'.format(unquote(username), unquote(password)),
        encoding=auth_encoding
    )).strip()


def get_proxy(auth_encoding, url: str, orig_type: str) -> Tuple[bytes, str]:
    proxy_type, user, password, host_port = _parse_proxy(url)
    proxy_url: str = urlunparse((
        proxy_type or orig_type, host_port, '', '', '', ''
    ))
    credentials: bytes = (
        basic_auth_header(user, password, auth_encoding)
        if user else None
    )
    return credentials, proxy_url


def inspect_block(
        block_inspector_mw,
        request: Request = None,
        response: Response = None,
        exception: Exception = None,
        spider: Spider = None
) -> Any:
    for result in _inspect_block(
            block_inspector_mw, request, response, exception, spider
    ):
        if result:
            return result


def _inspect_block(
        block_inspector_mw,
        request: Request = None,
        response: Response = None,
        exception: Exception = None,
        spider: Spider = None
) -> Generator[Any, None, None]:
    if response and response.status in block_inspector_mw.settings.getlist(
            'HTTPPROXY_PROXY_INVALIDATED_STATUS_CODES'
    ):
        yield response.status
    if exception in block_inspector_mw.settings.getlist(
            'HTTPPROXY_PROXY_INVALIDATED_EXCEPTIONS'
    ):
        yield exception


def recycle_request(
        block_inspector_mw, request: Request, spider: Spider
) -> Request:
    # req = deepcopy(request)
    req = copy(request)
    try:
        req.meta.pop('proxy')
    except KeyError as exc:
        pass
    try:
        req.headers.pop('Proxy-Authorization')
    except KeyError as exc:
        pass

    req.dont_filter = True
    req.priority = req.priority + block_inspector_mw.settings.getint(
        'RETRY_PRIORITY_ADJUST'
    )
    return req
