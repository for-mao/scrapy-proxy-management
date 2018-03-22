import re
from typing import Generator

from scrapy.http import Response

pattern_recaptcha = re.compile(
    r'(?P<recaptcha_api>www\.google\.com/recaptcha/api\.js)',
    flags=re.VERBOSE
)


class GoogleRecaptchaException(Exception):
    pass


def _inspect_google_recaptcha(
        response: Response
) -> Generator[bool, None, None]:
    for _ in map(lambda x: pattern_recaptcha.search(x),
                 response.css('script::attr(src)').extract()):
        yield _


def inspect_google_recaptcha(response: Response):
    if any(_inspect_google_recaptcha(response)):
        raise GoogleRecaptchaException
