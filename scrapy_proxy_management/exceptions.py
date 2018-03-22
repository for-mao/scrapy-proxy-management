# ------------------------------------------------------------------------------
# BLOCK INSPECTOR IN DOWNLOADER & SPIDER MIDDLEWARES
# ------------------------------------------------------------------------------


class ProxyBlockException(Exception):
    def __init__(self, response):
        self.response = response


class ProxyExhaustedException(Exception):
    pass


class StorageNotSupportException(Exception):
    pass
