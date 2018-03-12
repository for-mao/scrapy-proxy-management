HTTPPROXY_ENABLED = False
HTTPPROXY_AUTH_ENCODING = 'latin-1'

HTTPPROXY_PROXY_BYPASS_LRU_CACHE = 2 ** 10

# ------------------------------------------------------------------------------
# Environment Proxy Storage
# ------------------------------------------------------------------------------

HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.environment_http_proxy.EnvironmentProxyStorage'

# ------------------------------------------------------------------------------
# Settings Proxy Storage
# ------------------------------------------------------------------------------

# HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.settings_http_proxy.SettingsProxyStorage'

HTTPPROXY_PROXIES = {
    'http': [],
    'https': [],
    'no': [],
}

# ------------------------------------------------------------------------------
# MongoDB Proxy Storage
# ------------------------------------------------------------------------------

# HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.mongodb_http_proxy.MongoDBSyncProxyStorage'

# HTTPPROXY_MONGODB_USERNAME =
# HTTPPROXY_MONGODB_PASSWORD =

HTTPPROXY_MONGODB_HOST = 'localhost'
HTTPPROXY_MONGODB_PORT = 27017

# HTTPPROXY_MONGODB_OPTIONS_ =

HTTPPROXY_MONGODB_DATABASE = 'scrapy_proxies'
HTTPPROXY_MONGODB_COLLECTION = 'proxies'

HTTPPROXY_MONGODB_AUTHSOURCE = HTTPPROXY_MONGODB_DATABASE

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

HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC = 'scrapy_proxy_management.extensions.mongodb_http_proxy.get_proxy_from_doc'

HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY = 'scrapy_proxy_management.extensions.strategies.default_proxy_management_strategy.DefaultProxyManagementStrategy'
