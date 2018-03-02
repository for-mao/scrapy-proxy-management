HTTPPROXY_ENABLED = False
HTTPPROXY_AUTH_ENCODING = 'latin-1'

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
