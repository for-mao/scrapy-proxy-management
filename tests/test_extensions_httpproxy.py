from unittest import TestCase

import base64

from scrapy import Request
from scrapy.http import Response
from scrapy.settings import Settings
from scrapy.spiders import Spider

from scrapy_proxy_management.extensions import ProxyStorage


class ProxyStorageTest(TestCase):
    def setUp(self):
        self.settings = Settings()
        self.storage = ProxyStorage(
            settings=self.settings,
            auth_encoding='latin-1'
        )

    def test__get_proxy(self):
        proxies = [
            {'proxy': ['http://username:password@proxy.com', 'http'],
             'result': (base64.b64encode(bytes(
                 '{}:{}'.format('username', 'password'),
                 encoding=self.storage.auth_encoding
             )).strip(), 'http://proxy.com')},
            {'proxy': ['https://username:password@proxy.com', 'https'],
             'result': (base64.b64encode(bytes(
                 '{}:{}'.format('username', 'password'),
                 encoding=self.storage.auth_encoding
             )).strip(), 'https://proxy.com')},
            {'proxy': ['http://proxy.com', 'http'],
             'result': (None, 'http://proxy.com')},
            {'proxy': ['https://proxy.com', 'https'],
             'result': (None, 'https://proxy.com')},
        ]
        for proxy in proxies:
            self.assertSequenceEqual(
                self.storage._get_proxy(*proxy['proxy']),
                proxy['result']
            )

    def test__basic_auth_header(self):
        username = 'username'
        password = 'password'

        credentials = base64.b64encode(bytes(
            '{}:{}'.format(username, password),
            encoding=self.storage.auth_encoding
        )).strip()

        self.assertEqual(
            self.storage._basic_auth_header(
                username=username, password=password
            ),
            credentials
        )

    def test_open_spider(self):
        spider = Spider('foo')
        self.assertRaises(
            NotImplementedError,
            self.storage.open_spider,
            spider=spider
        )

    def test_close_spider(self):
        spider = Spider('foo')
        self.assertRaises(
            NotImplementedError,
            self.storage.close_spider,
            spider=spider
        )

    def test_proxy_invalidated(self):
        spider = Spider('foo')
        self.assertRaises(
            NotImplementedError,
            self.storage.invalidate_proxy,
            request=Request('http://test.usage'),
            response=Response('http://test.usage'),
            spider=spider
        )

    def test_retrieve_proxy(self):
        self.assertRaises(
            NotImplementedError,
            self.storage.retrieve_proxy,
            scheme='http'
        )
