.. _topics-storage:

=======
Storage
=======

The storage is a framework of hooks into Scrapy's downloader middleware. It's a
light, low-level system for downloader middleware to interact with the source
stored proxies.

Write your own storage
======================

Each storage component is a Python class that defines the following methods:

.. module:: scrapy_proxy_management.extensions

.. class:: Storage

   .. note::  Any of the storage methods should return synchronously.

   .. method:: open_spider(spider)

      :param spider:
          :type spider: :class:`~scrapy.spiders.Spider` object

   .. method:: close_spider(spider)

      :param spider:
          :type spider: :class:`~scrapy.spiders.Spider` object

   .. method:: invalidate_proxy(request, response, exception, spider, **kwargs)

      :param request:
          :type request: :class:`~scrapy.http.Request` object

      :param response:
          :type response: :class:`~scrapy.http.Response` object

      :param exception:
          :type exception: :class:`Exception` object

      :param spider:
          :type spider: :class:`~scrapy.spiders.Spider` object

   .. method:: load_proxies_from_source()

   .. method:: proxy_bypass(host, proxies)

      :param host:
          :type host:

          :param proxies:
          :type proxies:

       .. method:: retrieve_proxy(scheme, spider)

      :param spider:
          :type spider: :class:`~scrapy.spiders.Spider` object

Built-in storage reference
==========================

.. _storage-Environment:

Environment
-----------

.. module:: scrapy_proxy_management.extensions.environment_http_proxy
:synopsis: Environment Proxy Storage

.. class:: EnvironmentProxyStorage

.. _storage-settings.py:

settings.py
-----------

.. module:: scrapy_proxy_management.extensions.settings_http_proxy
:synopsis: Settings Proxy Storage

.. class:: SettingsProxyStorage

The following settings can be used to configure the cookie middleware:

* :setting:`HTTPPROXY_PROXIES`

.. _storage-MongoDB:

MongoDB
-------

.. module:: scrapy_proxy_management.extensions.mongodb_http_proxy
:synopsis: Settings Proxy Storage

.. class:: MongoDBSyncProxyStorage

The following settings can be used to configure the cookie middleware:

* :setting:`HTTPPROXY_MONGODB_USERNAME`
* :setting:`HTTPPROXY_MONGODB_PASSWORD`
* :setting:`HTTPPROXY_MONGODB_HOST`
* :setting:`HTTPPROXY_MONGODB_PORT`
* :setting:`HTTPPROXY_MONGODB_OPTIONS_*`
* :setting:`HTTPPROXY_MONGODB_DATABASE`
* :setting:`HTTPPROXY_MONGODB_COLLECTION`
* :setting:`HTTPPROXY_MONGODB_AUTHSOURCE`
* :setting:`HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS`
* :setting:`HTTPPROXY_MONGODB_PROXY_RETRIEVER`
* :setting:`HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC`
* :setting:`HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY`
