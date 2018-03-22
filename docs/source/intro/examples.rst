.. _intro-examples:

========
Examples
========

This downloader middleware supports many proxy storage.

Use The Proxies From Environment Variables (Default)
====================================================

This storage is compatible with the scrapy original httpproxy downloader
middleware::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   # replace the original httpproxy downloader middelware in-place
   DOWNLOADER_MIDDLEWARES.update({
       'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
       'scrapy_proxy_management.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750
   })

   HTTPPROXY_ENABLED = True

That is it - as simple as the original downloader middleware.

Use The Proxies From settings.py
================================

This storage is using the the proxies from the settings.py::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   # replace the original httpproxy downloader middelware in-place
   DOWNLOADER_MIDDLEWARES.update({
       'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
       'scrapy_proxy_management.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750
   })

   HTTPPROXY_ENABLED = True

   HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.settings_http_proxy.SettingsProxyStorage'

   HTTPPROXY_PROXIES = {
       'http': [
           'http://username:password@proxy01.com',
           'http://username:password@proxy02.com',
       ],
       'https': [
           'https://username:password@proxy01.com',
           'https://username:password@proxy02.com',
       ],
       'no': [
           'noproxy01.com',
           'noproxy02.com',
       ],
   }

Use The Proxies From MongoDB
============================

This storage is using the the proxies from MongoDB::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   # replace the original httpproxy downloader middleware in-place
   DOWNLOADER_MIDDLEWARES.update({
       'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
       'scrapy_proxy_management.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750
   })

   HTTPPROXY_ENABLED = True

   HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.mongodb_http_proxy.MongoDBProxyStorage'

   HTTPPROXY_MONGODB_USERNAME = 'username'
   HTTPPROXY_MONGODB_PASSWORD = 'password'

   HTTPPROXY_MONGODB_HOST = 'localhost'
   HTTPPROXY_MONGODB_PORT = 27017

   HTTPPROXY_MONGODB_DATABASE = 'scrapy_proxies'
   HTTPPROXY_MONGODB_COLLECTION = 'proxies'

   HTTPPROXY_MONGODB_AUTHSOURCE = HTTPPROXY_MONGODB_DATABASE

   # if any parameters added in settings.py but not belongs to mongoclient,
   # add it here
   HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS = {
       'collection',
       'database',
       'get_proxy_from_doc',
       'not_mongoclient_parameters',
       'proxy_management_strategy',
       'proxy_retriever',
   }

   # the method used to retrieve the proxies from the collection
   HTTPPROXY_MONGODB_PROXY_RETRIEVER = {
       'name': 'find',
       'filter': None,
       'projection': {
           '_id': 1,
           'scheme': 1,
           'proxy': 1,
           'username': 1,
           'password': 1
       },
       'skip': 0,
       'limit': 0,
       'sort': None
   }

   # the method to extract proxy from each document in the collection
   HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC = 'scrapy_proxy_management.extensions.mongodb_http_proxy.get_proxy_from_doc'

   # the strategy of the proxy management
   HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY = 'scrapy_proxy_management.extensions.strategies.default_proxy_management_strategy.DefaultProxyManagementStrategy'

