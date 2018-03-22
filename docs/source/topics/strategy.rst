.. _topics-strategy:

========
Strategy
========

The strategy is a framework of hooks into Storage. It defines the way how to use
the proxies from the storage. The main purpose of this object is:

* Decide which proxy should be provided when the middleware asks

* Decide what to do when current proxies list have been iterated to the end

* Decide how to manage the invalidated proxies

* Decide how to reload the proxies (e.g. exclusive the invalidated proxies)

Activating a strategy
=====================

To activate a strategy, set the `HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY`
setting.

Here's an example::

   HTTPPROXY_MONGODB_PROXY_MANAGEMENT_STRATEGY = 'scrapy_proxy_management.extensions.strategies.default_strategy.DefaultStrategy'

Writing your own strategy
=========================

Each strategy component is a Python class that defines the following methods:

.. module:: scrapy_proxy_management.extensions.strategies

.. class:: Strategy

   .. note::  Any of the strategy methods should return synchronously.

   .. method:: open_spider(spider)

      This method is called by the storage when the spider is opened.

      The intention of this method is to make the storage load the proxies from
      the source (initial the proxy pool).

   .. method:: close_spider(spider)

      This method is called by the storage when the spider is closed.

      The intention of this method is to do some cleaning up staff or export
      some usage report when the spider is closed.

   .. method:: invalidate_proxy(request, response, exception, spider, **kwargs)

      This method is called when a proxy is reported as blocked.

      The intention of this method is to deal with the invalidated proxy
      reported by other components through signals and the storage (e.g.
      block the invalidated proxy for ever, or just for a certain period).

   .. method:: reload_proxies(spider)

      This method is called when the proxy pool is iterated to the end.

      The intention of this method is to control the reload method when the
      proxy pool is iterated to the end (e.g. remove the proxy reported
      invalidated before).

      :meth:`reload_proxies` should return a dict with the same structure with
      the `storage.proxies`.

   .. method:: retrieve_proxy(scheme, spider)

      This method is called for a proxy with specified scheme.

      The intention of this method is to decide which proxy should be provided
      to this method caller.

      :meth:`retrieve_proxy` should return a tuple contained two elements:
      credential (bytes) and proxy (str), which keeps compatible with the
      httpproxy downloader middleware of scrapy.

Built-in strategy reference
===========================

This section describes all strategies that come with scrapy-proxy-management.
For information on how to use them and how to write your own strategy, see the
:ref:`strategy usage guide <topics-strategy>`.

.. _strategy-DefaultStrategy:

DefaultStrategy
------------------------------

.. module:: scrapy_proxy_management.extensions.strategies
:synopsis: Default Strategy

.. class:: DefaultStrategy

   This strategy enables the following simple proxy management:

   * load the proxy to a proxy pool from the source when the spider is opened
     (only load once in the whole life of the spider)

   * provide the proxy one by one based on the scheme

   * put the invalidated proxy into a container (actually a set), and never
     release

   * reload the proxy when the proxy pool is iterated to the end, and remove the
     invalidated proxies collected before

No settings require to configure this strategy.
