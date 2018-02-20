from contextlib import contextmanager

from scrapy.settings import Settings


@contextmanager
def unfreeze_settings(settings: Settings):
    original_status = settings.frozen
    settings.frozen = False
    yield
    settings.frozen = original_status
