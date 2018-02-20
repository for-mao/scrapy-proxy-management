import os
from functools import partial
from typing import Dict

from scrapy.crawler import Crawler
from scrapy.exceptions import NotConfigured
from scrapy.http import Request
from scrapy.settings import Settings
from scrapy.spiders import Spider
from twisted.trial.unittest import TestCase

from scrapy_proxy_management.downloadermiddlewares.httpproxy import \
    HttpProxyMiddleware

spider = Spider('foo')


class TestDefaultHttpProxyMiddleware(TestCase):
    failureException = AssertionError

    def setUp(self):
        self._oldenv = os.environ.copy()

    def tearDown(self):
        os.environ = self._oldenv

    def test_not_enabled(self):
        settings: Settings = Settings({'HTTPPROXY_ENABLED': False})
        crawler: Crawler = Crawler(spider, settings)
        self.assertRaises(
            NotConfigured,
            partial(HttpProxyMiddleware.from_crawler, crawler)
        )

    def test_no_environment_proxies(self):
        os.environ: Dict[str, str] = {
            'dummy_proxy': 'reset_env_and_do_not_raise'
        }
        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw: HttpProxyMiddleware = HttpProxyMiddleware(crawler=crawler)

        for url in ('http://e.com', 'https://e.com', 'file:///tmp/a'):
            req = Request(url)
            self.assertIsNone(mw.process_request(req, spider))
            self.assertEqual(req.url, url)
            self.assertEqual(req.meta, {})

    def test_environment_proxies(self):
        os.environ['http_proxy'] = http_proxy = 'https://proxy.for.http:3128'
        os.environ['https_proxy'] = https_proxy = 'http://proxy.for.https:8080'
        os.environ.pop('file_proxy', None)

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        for url, proxy in [('http://e.com', http_proxy),
                           ('https://e.com', https_proxy),
                           ('file://tmp/a', None)]:
            req = Request(url)
            self.assertIsNone(mw.process_request(req, spider))
            self.assertEqual(req.url, url)
            self.assertEqual(req.meta.get('proxy'), proxy)

    def test_proxy_precedence_meta(self):
        os.environ['http_proxy'] = 'https://proxy.com'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        req = Request('http://scrapytest.org',
                      meta={'proxy': 'https://new.proxy:3128'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://new.proxy:3128'})

    def test_proxy_auth(self):
        os.environ['http_proxy'] = 'https://user:pass@proxy:3128'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        req = Request('http://scrapytest.org')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic dXNlcjpwYXNz')
        # proxy from request.meta
        req = Request('http://scrapytest.org',
                      meta={'proxy': 'https://username:password@proxy:3128'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic dXNlcm5hbWU6cGFzc3dvcmQ=')

    def test_proxy_auth_empty_passwd(self):
        os.environ['http_proxy'] = 'https://user:@proxy:3128'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        req = Request('http://scrapytest.org')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic dXNlcjo=')
        # proxy from request.meta
        req = Request('http://scrapytest.org',
                      meta={'proxy': 'https://username:@proxy:3128'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic dXNlcm5hbWU6')

    def test_proxy_auth_encoding(self):
        # utf-8 encoding
        os.environ['http_proxy'] = u'https://m\u00E1n:pass@proxy:3128'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler, auth_encoding='utf-8')

        req = Request('http://scrapytest.org')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic bcOhbjpwYXNz')

        # proxy from request.meta
        req = Request('http://scrapytest.org',
                      meta={'proxy': u'https://\u00FCser:pass@proxy:3128'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic w7xzZXI6cGFzcw==')

        # default latin-1 encoding
        mw = HttpProxyMiddleware(crawler, auth_encoding='latin-1')
        req = Request('http://scrapytest.org')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic beFuOnBhc3M=')

        # proxy from request.meta, latin-1 encoding
        req = Request('http://scrapytest.org',
                      meta={'proxy': u'https://\u00FCser:pass@proxy:3128'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'https://proxy:3128'})
        self.assertEqual(req.headers.get('Proxy-Authorization'),
                         b'Basic /HNlcjpwYXNz')

    def test_proxy_already_seted(self):
        os.environ['http_proxy'] = 'https://proxy.for.http:3128'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        req = Request('http://noproxy.com', meta={'proxy': None})
        self.assertIsNone(mw.process_request(req, spider))
        assert 'proxy' in req.meta and req.meta['proxy'] is None

    def test_no_proxy(self):
        os.environ['http_proxy'] = 'https://proxy.for.http:3128'

        settings: Settings = Settings()
        crawler: Crawler = Crawler(spider, settings)
        mw = HttpProxyMiddleware(crawler)

        os.environ['no_proxy'] = '*'
        req = Request('http://noproxy.com')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertNotIn('proxy', req.meta)

        os.environ['no_proxy'] = 'other.com'
        req = Request('http://noproxy.com')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertIn('proxy', req.meta)

        os.environ['no_proxy'] = 'other.com,noproxy.com'
        req = Request('http://noproxy.com')
        self.assertIsNone(mw.process_request(req, spider))
        self.assertNotIn('proxy', req.meta)

        # proxy from meta['proxy'] takes precedence
        os.environ['no_proxy'] = '*'
        req = Request('http://noproxy.com', meta={'proxy': 'http://proxy.com'})
        self.assertIsNone(mw.process_request(req, spider))
        self.assertEqual(req.meta, {'proxy': 'http://proxy.com'})
