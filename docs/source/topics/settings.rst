.. _topics-settings:

========
Settings
========

.. _topics-settings-ref:

Built-in settings reference
===========================

.. setting:: HTTPPROXY_ENABLED

HTTPPROXY_ENABLED
-----------------

Default: ``False``

.. setting:: HTTPPROXY_AUTH_ENCODING

HTTPPROXY_AUTH_ENCODING
-----------------------

Default: ``latin-1``

.. setting:: HTTPPROXY_PROXY_BYPASS_LRU_CACHE

HTTPPROXY_PROXY_BYPASS_LRU_CACHE
--------------------------------

Default: ``1024``

.. setting:: HTTPPROXY_STORAGE

HTTPPROXY_STORAGE
-----------------

Default: ``'scrapy_proxy_management.extensions.environment_http_proxy.EnvironmentProxyStorage'``

.. setting:: HTTPPROXY_PROXIES

HTTPPROXY_PROXIES
-----------------

Default::

    {
        'http': [],
        'https': [],
        'no': [],
    }

.. setting:: HTTPPROXY_MONGODB_USERNAME

HTTPPROXY_MONGODB_USERNAME
--------------------------

Default: ``None``

.. setting:: HTTPPROXY_MONGODB_PASSWORD

HTTPPROXY_MONGODB_PASSWORD
--------------------------

Default: ``None``

.. setting:: HTTPPROXY_MONGODB_HOST

HTTPPROXY_MONGODB_HOST
----------------------

Default: ``'localhost'``

.. setting:: HTTPPROXY_MONGODB_PORT

HTTPPROXY_MONGODB_PORT
----------------------

Default: ``27017``

.. setting:: HTTPPROXY_MONGODB_OPTIONS_*

HTTPPROXY_MONGODB_OPTIONS_*
---------------------------

Default: ``None``

.. setting:: HTTPPROXY_MONGODB_DATABASE

HTTPPROXY_MONGODB_DATABASE
--------------------------

Default: ``'scrapy_proxies'``

.. setting:: HTTPPROXY_MONGODB_COLLECTION

HTTPPROXY_MONGODB_COLLECTION
----------------------------

Default: ``'proxies'``

.. setting:: HTTPPROXY_MONGODB_AUTHSOURCE

HTTPPROXY_MONGODB_AUTHSOURCE
----------------------------

Default: ``'proxies'``

.. setting:: HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS

HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS
--------------------------------------------

Default::

    {
        'collection',
        'database',
        'get_proxy_from_doc',
        'not_mongoclient_parameters',
        'proxy_management_strategy',
        'proxy_retriever',
    }

.. setting:: HTTPPROXY_MONGODB_PROXY_RETRIEVER

HTTPPROXY_MONGODB_PROXY_RETRIEVER
---------------------------------

Default::

    {
        'name': 'find',
        'filter': None,
        'projection': {
            '_id': 1, 'scheme': 1, 'proxy': 1, 'username': 1, 'password': 1
        },
        'skip': 0,
        'limit': 0,
        'sort': None
    }

.. setting:: HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC

HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC
------------------------------------

Default: ``'scrapy_proxy_management.extensions.mongodb_http_proxy.get_proxy_from_doc'``

.. setting:: HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY

HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY
-------------------------------------------

Default: ``'scrapy_proxy_management.extensions.strategies.default_strategy.DefaultStrategy'``
