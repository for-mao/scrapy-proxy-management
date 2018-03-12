import os
from contextlib import contextmanager
from copy import deepcopy
from functools import partial
from typing import Dict
from urllib.parse import urlparse

from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.spiders import Spider
from twisted.trial.unittest import TestCase

from scrapy_proxy_management.downloadermiddlewares.httpproxy import \
    HttpProxyMiddleware

_spider = Spider('foo')


@contextmanager
def _open_spider(
        spider: Spider,
        settings: Settings,
        auth_encoding: str = 'latin-1'
):
    crawler = Crawler(spider, settings)
    middleware = HttpProxyMiddleware(
        crawler=crawler, auth_encoding=auth_encoding
    )

    middleware.spider_opened(spider)

    try:
        yield middleware
    finally:
        middleware.spider_closed(spider)


class TestDefaultHttpProxyMiddleware(TestCase):
    failureException = AssertionError

    def setUp(self):
        self._oldenv = os.environ.copy()

    def tearDown(self):
        os.environ = self._oldenv

    def test_not_enabled(self):
        settings: Settings = Settings({'HTTPPROXY_ENABLED': False})
        crawler: Crawler = Crawler(_spider, settings)
        self.assertRaises(
            NotConfigured,
            partial(HttpProxyMiddleware.from_crawler, crawler)
        )

    def test_no_environment_proxies(self):
        os.environ: Dict[str, str] = {
            'dummy_proxy': 'reset_env_and_do_not_raise'
        }

        with _open_spider(_spider, Settings()) as mw:
            for url in ('http://e.com', 'https://e.com', 'file:///tmp/a'):
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta, {})

    def test_environment_proxies(self):
        os.environ['http_proxy'] = http_proxy = 'https://proxy.for.http:3128'
        os.environ['https_proxy'] = https_proxy = 'http://proxy.for.https:8080'
        os.environ.pop('file_proxy', None)

        with _open_spider(_spider, Settings()) as mw:
            for url, proxy in [('http://e.com', http_proxy),
                               ('https://e.com', https_proxy),
                               ('file://tmp/a', None)]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)

    def test_proxy_precedence_meta(self):
        os.environ['http_proxy'] = 'https://proxy.com'

        with _open_spider(_spider, Settings()) as mw:
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://new.proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://new.proxy:3128'})

    def test_proxy_auth(self):
        os.environ['http_proxy'] = 'https://user:pass@proxy:3128'

        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic dXNlcjpwYXNz'
            )
            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://username:password@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
            )

    def test_proxy_auth_empty_passwd(self):
        os.environ['http_proxy'] = 'https://user:@proxy:3128'

        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic dXNlcjo='
            )
            # proxy from request.meta
            req = Request('http://scrapytest.org',
                          meta={'proxy': 'https://username:@proxy:3128'})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic dXNlcm5hbWU6'
            )

    def test_proxy_auth_encoding(self):
        # utf-8 encoding
        os.environ['http_proxy'] = u'https://m\u00E1n:pass@proxy:3128'

        with _open_spider(_spider, Settings(), auth_encoding='utf-8') as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic bcOhbjpwYXNz'
            )

            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': u'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic w7xzZXI6cGFzcw=='
            )

        with _open_spider(_spider, Settings()) as mw:
            # default latin-1 encoding
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic beFuOnBhc3M='
            )

            # proxy from request.meta, latin-1 encoding
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': u'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic /HNlcjpwYXNz'
            )

    def test_proxy_already_seted(self):
        os.environ['http_proxy'] = 'https://proxy.for.http:3128'

        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://noproxy.com', meta={'proxy': None})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertTrue('proxy' in req.meta)
            self.assertIsNone(req.meta['proxy'])

    def test_no_proxy(self):
        os.environ['http_proxy'] = 'https://proxy.for.http:3128'

        # test 1
        os.environ['no_proxy'] = '*'
        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 2
        os.environ['no_proxy'] = 'other.com'
        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertIn('proxy', req.meta)

        # test 3
        os.environ['no_proxy'] = 'other.com,noproxy.com'
        with _open_spider(_spider, Settings()) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 4, proxy from meta['proxy'] takes precedence
        os.environ['no_proxy'] = '*'
        with _open_spider(_spider, Settings()) as mw:
            req = Request(
                'http://noproxy.com', meta={'proxy': 'http://proxy.com'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'http://proxy.com'})

    def test_invalidate_proxy(self):
        os.environ['http_proxy'] = http_proxy = 'https://proxy.for.http:3128'
        os.environ['https_proxy'] = https_proxy = 'http://proxy.for.https:8080'
        os.environ.pop('file_proxy', None)

        with _open_spider(_spider, Settings()) as mw:
            request = Request('http://e.com')
            self.assertRaises(
                NotImplementedError,
                mw.proxy_invalidated, spider=_spider, request=request
            )


class TestSettingsHttpProxyMiddleware(TestCase):
    settings = {
        'HTTPPROXY_STORAGE': 'scrapy_proxy_management.extensions.settings_http_proxy.SettingsProxyStorage',
    }

    def test_no_proxies(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {}
        })

        with _open_spider(_spider, settings) as mw:
            for url in ('http://e.com', 'https://e.com', 'file:///tmp/a'):
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta, {})

    def test_proxies(self):
        http_proxy_1 = 'https://proxy.for.http.1:3128'
        http_proxy_2 = 'https://proxy.for.http.2:3128'
        https_proxy_1 = 'http://proxy.for.https.1:8080'
        https_proxy_2 = 'http://proxy.for.https.2:8080'

        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {
                'http': [http_proxy_1, http_proxy_2],
                'https': [https_proxy_1, https_proxy_2]
            }
        })

        with _open_spider(_spider, settings) as mw:
            for url, proxy in [('http://e.com', http_proxy_1),
                               ('https://e.com', https_proxy_1),
                               ('file://tmp/a', None)]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [('http://e.com', http_proxy_2),
                               ('https://e.com', https_proxy_2),
                               ('file://tmp/a', None)]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [('http://e.com', http_proxy_1),
                               ('https://e.com', https_proxy_1),
                               ('file://tmp/a', None)]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [('http://e.com', http_proxy_2),
                               ('https://e.com', https_proxy_2),
                               ('file://tmp/a', None)]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)

    def test_proxy_precedence_meta(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'https': ['https://proxy.com']}
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://scrapytest.org',
                          meta={'proxy': 'https://new.proxy:3128'})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://new.proxy:3128'})

    def test_proxy_auth(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'http': ['https://user:pass@proxy:3128']}
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic dXNlcjpwYXNz'
            )
            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://username:password@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
            )

    def test_proxy_auth_empty_passwd(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'http': ['https://user:@proxy:3128']}
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(req.headers.get('Proxy-Authorization'),
                             b'Basic dXNlcjo=')
            # proxy from request.meta
            req = Request('http://scrapytest.org',
                          meta={'proxy': 'https://username:@proxy:3128'})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(req.headers.get('Proxy-Authorization'),
                             b'Basic dXNlcm5hbWU6')

    def test_proxy_auth_encoding(self):
        # utf-8 encoding
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'http': ['https://m\u00E1n:pass@proxy:3128']}
        })

        with _open_spider(_spider, settings, auth_encoding='utf-8') as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic bcOhbjpwYXNz'
            )

            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': u'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic w7xzZXI6cGFzcw=='
            )

        with _open_spider(_spider, settings) as mw:
            # default latin-1 encoding
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic beFuOnBhc3M='
            )

            # proxy from request.meta, latin-1 encoding
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': u'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic /HNlcjpwYXNz'
            )

    def test_proxy_already_seted(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'http': ['https://proxy.for.http:3128']}
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://noproxy.com', meta={'proxy': None})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertTrue('proxy' in req.meta)
            self.assertIsNone(req.meta['proxy'])

    def test_no_proxy(self):
        settings: Dict = {
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {'http': ['https://proxy.for.http:3128']}
        }

        # test 1
        _settings = deepcopy(settings)
        _settings['HTTPPROXY_PROXIES'].update({'no': ['*']})

        settings: Settings = Settings(_settings)

        with _open_spider(_spider, settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 2
        _settings = deepcopy(settings)
        _settings['HTTPPROXY_PROXIES'].update({'no': ['other.com']})

        settings: Settings = Settings(_settings)

        with _open_spider(_spider, settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertIn('proxy', req.meta)

        # test 3
        _settings = deepcopy(settings)
        _settings['HTTPPROXY_PROXIES'].update({
            'no': ['other.com', 'noproxy.com']
        })

        settings: Settings = Settings(_settings)

        with _open_spider(_spider, settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 4, proxy from meta['proxy'] takes precedence
        _settings = deepcopy(settings)
        _settings['HTTPPROXY_PROXIES'].update({'no': ['*']})

        settings: Settings = Settings(_settings)

        with _open_spider(_spider, settings) as mw:
            req = Request(
                'http://noproxy.com', meta={'proxy': 'http://proxy.com'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'http://proxy.com'})

    def test_invalidate_proxy(self):
        http_proxy_1 = 'http://proxy.for.https.1:8080'
        http_proxy_2 = 'http://proxy.for.https.2:8080'
        https_proxy_1 = 'https://proxy.for.http.1:3128'
        https_proxy_2 = 'https://proxy.for.http.2:3128'

        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_ENABLED': True,
            'HTTPPROXY_PROXIES': {
                'http': [http_proxy_1, http_proxy_2],
                'https': [https_proxy_1, https_proxy_2]
            }
        })

        with _open_spider(_spider, settings) as mw:
            request = Request('http://e.com')
            self.assertRaises(
                NotImplementedError,
                mw.proxy_invalidated, spider=_spider, request=request
            )


class TestMongoDBHttpProxyMiddleware(TestCase):
    settings = {
        'HTTPPROXY_STORAGE': 'scrapy_proxy_management.extensions.mongodb_http_proxy.MongoDBSyncProxyStorage',

        'HTTPPROXY_ENABLED': True,

        'HTTPPROXY_MONGODB_USERNAME': 'test',
        'HTTPPROXY_MONGODB_PASSWORD': 'test',

        'HTTPPROXY_MONGODB_HOST': 'localhost',
        'HTTPPROXY_MONGODB_PORT': 27017,

        'HTTPPROXY_MONGODB_DATABASE': 'scrapy_proxy_management',
    }

    proxy_retrieve = {
        'name': 'find',
        'filter': None,
        'projection': {
            '_id': 1,
            'scheme': 1, 'proxy': 1,
            'username': 1, 'password': 1
        },
        'skip': 0,
        'limit': 0,
        'sort': None
    }

    def test_no_proxies(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_empty',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            for url in ('http://e.com', 'https://e.com', 'file:///tmp/a'):
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta, {})

    def test_proxies(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            for url, proxy in [
                ('http://e.com', 'https://proxy.for.http.1:3128'),
                ('https://e.com', 'http://proxy.for.https.1:8080'),
                ('file://tmp/a', None)
            ]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [
                ('http://e.com', 'https://proxy.for.http.2:3128'),
                ('https://e.com', 'http://proxy.for.https.2:8080'),
                ('file://tmp/a', None)
            ]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [
                ('http://e.com', 'https://proxy.for.http.1:3128'),
                ('https://e.com', 'http://proxy.for.https.1:8080'),
                ('file://tmp/a', None)
            ]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)
            for url, proxy in [
                ('http://e.com', 'https://proxy.for.http.2:3128'),
                ('https://e.com', 'http://proxy.for.https.2:8080'),
                ('file://tmp/a', None)
            ]:
                req = Request(url)
                self.assertIsNone(mw.process_request(req, _spider))
                self.assertEqual(req.url, url)
                self.assertEqual(req.meta.get('proxy'), proxy)

    def test_proxy_precedence_meta(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://new.proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://new.proxy:3128'})

    def test_proxy_auth(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_auth',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic dXNlcjpwYXNz'
            )
            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://username:password@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic dXNlcm5hbWU6cGFzc3dvcmQ='
            )

    def test_proxy_auth_empty_passwd(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_auth_empty_passwd',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(req.headers.get('Proxy-Authorization'),
                             b'Basic dXNlcjo=')
            # proxy from request.meta
            req = Request('http://scrapytest.org',
                          meta={'proxy': 'https://username:@proxy:3128'})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(req.headers.get('Proxy-Authorization'),
                             b'Basic dXNlcm5hbWU6')

    def test_proxy_auth_encoding(self):
        # utf-8 encoding
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_auth_encoding',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings, auth_encoding='utf-8') as mw:
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic bcOhbjpwYXNz'
            )

            # proxy from request.meta
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': 'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'),
                b'Basic w7xzZXI6cGFzcw=='
            )

        with _open_spider(_spider, settings) as mw:
            # default latin-1 encoding
            req = Request('http://scrapytest.org')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic beFuOnBhc3M='
            )

            # proxy from request.meta, latin-1 encoding
            req = Request(
                'http://scrapytest.org',
                meta={'proxy': u'https://\u00FCser:pass@proxy:3128'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
            self.assertEqual(
                req.headers.get('Proxy-Authorization'), b'Basic /HNlcjpwYXNz'
            )

    def test_proxy_already_seted(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://noproxy.com', meta={'proxy': None})
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertTrue('proxy' in req.meta)
            self.assertIsNone(req.meta['proxy'])

    def test_no_proxy(self):
        settings: Dict = {
            **self.settings,
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        }

        # test 1
        _settings = deepcopy(settings)
        _settings.update({
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_no_proxy_1',
        })

        _settings: Settings = Settings(_settings)

        with _open_spider(_spider, _settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 2
        _settings = deepcopy(settings)
        _settings.update({
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_no_proxy_2',
        })

        _settings: Settings = Settings(_settings)

        with _open_spider(_spider, _settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertIn('proxy', req.meta)

        # test 3
        _settings = deepcopy(settings)
        _settings.update({
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_no_proxy_3',
        })

        _settings: Settings = Settings(_settings)

        with _open_spider(_spider, _settings) as mw:
            req = Request('http://noproxy.com')
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertNotIn('proxy', req.meta)

        # test 4, proxy from meta['proxy'] takes precedence
        _settings = deepcopy(settings)
        _settings.update({
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies_no_proxy_1',
        })

        _settings: Settings = Settings(_settings)

        with _open_spider(_spider, _settings) as mw:
            req = Request(
                'http://noproxy.com', meta={'proxy': 'http://proxy.com'}
            )
            self.assertIsNone(mw.process_request(req, _spider))
            self.assertEqual(req.meta, {'proxy': 'http://proxy.com'})

    def test_invalidate_proxy(self):
        settings: Settings = Settings({
            **self.settings,
            'HTTPPROXY_MONGODB_COLLECTION': 'proxies',
            'HTTPPROXY_MONGODB_PROXY_RETRIEVER': deepcopy(self.proxy_retrieve)
        })

        with _open_spider(_spider, settings) as mw:
            req = Request('http://e.com')
            mw.process_request(req, _spider)

            _proxy = (urlparse(req.url).scheme,
                      req.headers.get('Proxy-Authorization'),
                      req.meta['proxy'])

            self.assertIsNone(mw.proxy_invalidated(request=req, spider=_spider))

            self.assertIn(_proxy, mw.storage.proxies_invalidated)

            mw.storage.strategy.reload_proxies()

            self.assertNotIn(_proxy, mw.storage.proxies)
