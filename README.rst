=======================
Scrapy Proxy Management
=======================

.. image:: https://img.shields.io/pypi/v/scrapy-proxy-management.svg
   :target: https://pypi.python.org/pypi/scrapy-proxy-management
   :alt: PyPI Version

.. image:: https://img.shields.io/travis/grammy-jiang/scrapy-proxy-management/master.svg
   :target: http://travis-ci.org/grammy-jiang/scrapy-proxy-management
   :alt: Build Status

.. image:: https://img.shields.io/badge/wheel-yes-brightgreen.svg
   :target: https://pypi.python.org/pypi/scrapy-proxy-management
   :alt: Wheel Status

.. image:: https://img.shields.io/codecov/c/github/grammy-jiang/scrapy-proxy-management/master.svg
   :target: http://codecov.io/github/grammy-jiang/scrapy-proxy-management?branch=master
   :alt: Coverage report

.. .. image:: https://img.shields.io/github/downloads/grammy-jiang/scrapy-proxy-management/total.svg
   :target: https://github.com/grammy-jiang/scrapy-proxy-management
   :alt: Downloads

.. image:: https://img.shields.io/pypi/dm/scrapy-proxy-management.svg
   :target: https://github.com/grammy-jiang/scrapy-proxy-management
   :alt: Downloads

Overview
========

Scrapy is a great framework for web crawling. This middleware provides a proxy
rotation from many sources which define in the settings in settings.py, spider,
request.

Requirements
============

* Tests on Python 3.6

* Tests on Linux, but it's a pure python module - it should work on any other
platforms with official python supported, e.g. Windows, Mac OSX, BSD

Installation
============

The quick way::

    pip install scrapy-proxy-management

Documentation
=============

This middleware supports the following proxy storage ways:

* environment variables (compatible with the middleware provided by scrapy)

* settings.py

* MongoDB

The relative settings are followed:

Environment Variables
---------------------

This is the default setting in this middleware, which has the same behaviours
and settings with the middleware provided by scrapy::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.environment_http_proxy.EnvironmentProxyStorage' # default

   HTTPPROXY_ENABLED = True # default False
   HTTPPROXY_AUTH_ENCODING = 'latin-1' # default latin-1

settings.py
---------------------

This way allows scrapy using the proxies defined in the settings.py. This
middleware would use the proxies in a endless cycle::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.settings_http_proxy.SettingsProxyStorage'

   HTTPPROXY_ENABLED = True # default False
   HTTPPROXY_AUTH_ENCODING = 'latin-1' # default latin-1

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

MongoDB
---------------------

This way allows scrapy using the proxies saved in MongoDB. This middleware would
retrieve the proxies from MongoDB in a user-defined way::

   # ---------------------------------------------------------------------------
   # Proxy Management
   # ---------------------------------------------------------------------------

   HTTPPROXY_STORAGE = 'scrapy_proxy_management.extensions.mongodb_http_proxy.MongoDBProxyStorage'

   HTTPPROXY_ENABLED = True # default False
   HTTPPROXY_AUTH_ENCODING = 'latin-1' # default latin-1

   # HTTPPROXY_MONGODB_USERNAME =
   # HTTPPROXY_MONGODB_PASSWORD =

   HTTPPROXY_MONGODB_HOST = 'localhost'
   HTTPPROXY_MONGODB_PORT = 27017

   # HTTPPROXY_MONGODB_OPTIONS_ =

   HTTPPROXY_MONGODB_DATABASE = 'scrapy_proxies'
   HTTPPROXY_MONGODB_COLLECTION = 'proxies'

   HTTPPROXY_MONGODB_AUTHSOURCE = HTTPPROXY_MONGODB_DATABASE # default same with the database contained proxies

   HTTPPROXY_MONGODB_NOT_MONGOCLIENT_PARAMETERS = {
       'collection',
       'database',
       'get_proxy_from_doc',
       'not_mongoclient_parameters',
       'proxy_management_strategy',
       'proxy_retriever',
   } # if any parameters added in settings.py but not belongs to mongoclient, add it here

   HTTPPROXY_MONGODB_PROXY_RETRIEVER = {
       'name': 'find',
       'filter': None,
       'projection': {
           '_id': 1, 'scheme': 1, 'proxy': 1, 'username': 1, 'password': 1
       },
       'skip': 0,
       'limit': 0,
       'sort': None
   } # the method used to retrieve the proxies from the collection

   HTTPPROXY_MONGODB_GET_PROXY_FROM_DOC = 'scrapy_proxy_management.extensions.mongodb_http_proxy.get_proxy_from_doc' # the method to extract proxy from each document in the collection

   HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY = 'scrapy_proxy_management.extensions.strategies.default_proxy_management_strategy.DefaultProxyManagementStrategy' # the strategy of the proxy management

