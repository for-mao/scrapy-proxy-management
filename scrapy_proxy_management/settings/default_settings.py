HTTPPROXY_ENABLED = False
HTTPPROXY_AUTH_ENCODING = 'latin-1'

HTTPPROXY_PROXY_BYPASS_LRU_CACHE = 2 ** 10

HTTPPROXY_STRATEGY = 'scrapy_proxy_management.strategies.default_strategy.DefaultStrategy'

# ------------------------------------------------------------------------------
# Environment Proxy Storage
# ------------------------------------------------------------------------------

HTTPPROXY_STORAGE = 'scrapy_proxy_management.storages.environment_storage.EnvironmentStorage'

# ------------------------------------------------------------------------------
# Settings Proxy Storage
# ------------------------------------------------------------------------------

# HTTPPROXY_STORAGE = 'scrapy_proxy_management.storages.settings_storage.SettingsStorage'

HTTPPROXY_PROXIES = {
    'http': [],
    'https': [],
    # 'no' could be a list with domains
    'no': [],
    # or a string '*'
    # 'no': '*'
}

# ------------------------------------------------------------------------------
# MongoDB Proxy Storage
# ------------------------------------------------------------------------------

# HTTPPROXY_STORAGE = 'scrapy_proxy_management.storages.mongodb_storage.MongoDBSyncStorage'

# HTTPPROXY_MONGODB_USERNAME =
# HTTPPROXY_MONGODB_PASSWORD =

HTTPPROXY_MONGODB_HOST = 'localhost'
HTTPPROXY_MONGODB_PORT = 27017

# HTTPPROXY_MONGODB_OPTIONS_ =

HTTPPROXY_MONGODB_DATABASE = 'scrapy_proxies'
HTTPPROXY_MONGODB_COLLECTION = 'proxies'

HTTPPROXY_MONGODB_AUTHSOURCE = 'proxies'

HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS = {
    'collection',
    'database',
    'get_proxy_from_doc',
    'not_mongoclient_parameters',
    'proxy_management_strategy',
    'proxy_retriever',
}

HTTPPROXY_MONGODB_PROXY_RETRIEVER = {
    'name': 'find',
    'filter': None,
    'projection': {
        '_id': 1, 'scheme': 1, 'proxy': 1, 'username': 1, 'password': 1
    },
    'skip': 0,
    'limit': 0,
    'sort': None
}

HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC = 'scrapy_proxy_management.storages.mongodb_storage.get_proxy_from_doc'

# ------------------------------------------------------------------------------
# BLOCK INSPECTOR IN DOWNLOADER & SPIDER MIDDLEWARES
# ------------------------------------------------------------------------------

HTTPPROXY_PROXY_DM_BLOCK_INSPECTOR = 'scrapy_proxy_management.utils.inspect_block'
HTTPPROXY_PROXY_SM_BLOCK_INSPECTOR = 'scrapy_proxy_management.utils.inspect_block'

HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS = {
    'scrapy_proxy_management.signals.proxy_invalidated',
}
HTTPPROXY_PROXY_SM_BLOCK_INSPECTED_SIGNALS = {
    'scrapy_proxy_management.signals.proxy_invalidated',
}

HTTPPROXY_PROXY_DM_BLOCK_INSPECTED_SIGNALS_DEFERRED = set()
HTTPPROXY_PROXY_SM_BLOCK_INSPECTED_SIGNALS_DEFERRED = set()

HTTPPROXY_DM_RECYCLE_REQUEST = 'scrapy_proxy_management.utils.recycle_request'
HTTPPROXY_SM_RECYCLE_REQUEST = 'scrapy_proxy_management.utils.recycle_request'

HTTPPROXY_PROXY_INVALIDATED_STATUS_CODES = set()
HTTPPROXY_PROXY_INVALIDATED_EXCEPTIONS = {
    'twisted.internet.error.ConnectError',
    'twisted.internet.error.ConnectionLost',
    'twisted.internet.error.ConnectionRefusedError',
    'twisted.internet.error.TCPTimedOutError',
    'twisted.internet.error.TimeoutError',
}
