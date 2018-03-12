from contextlib import contextmanager
from typing import Any
from typing import Generator

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
    request.meta.pop('proxy')
    request.headers.pop('Proxy-Authorization')
    request.dont_filter = True
    request.priority = request.priority + block_inspector_mw.settings.getint(
        'RETRY_PRIORITY_ADJUST'
    )
    return request
