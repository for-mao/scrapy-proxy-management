from copy import deepcopy
from os.path import join

from scrapy.http import HtmlResponse
from scrapy.http import Request
from scrapy.http import Response
from scrapy.spiders import Spider
from scrapy.utils.test import get_crawler
from twisted.trial.unittest import TestCase

from scrapy_proxy_management.exceptions import ProxyBlockException
from scrapy_proxy_management.spidermiddlewares.block_inspector import \
    BlockInspectorMiddleware
from tests import tests_datadir


class OtherException(Exception):
    def __init__(self, response):
        self.response = response


def _responses(request):
    with open(join(tests_datadir, 'succeed.html'), mode='rb') as f:
        response_succeed = f.read()
    with open(join(tests_datadir, 'block.html'), mode='rb') as f:
        response_block = f.read()
    return [
        HtmlResponse(
            request.url, status=200, body=response_succeed, request=request,
        ),
        HtmlResponse(
            request.url, status=200, body=response_block, request=request,
        )
    ]


def inspect_block(
        mw: BlockInspectorMiddleware, response: Response, spider: Spider = None
):
    if response.css('#suspended').extract():
        return True
    else:
        return False


def _recycle_block_request(request):
    return request


class TestBlockInspector(TestCase):
    def setUp(self):
        self.req = Request('http://scrapytest.org')
        self.res_succeed, self.res_block = _responses(self.req)

        crawler = get_crawler(Spider, settings_dict={
            'HTTPPROXY_PROXY_SM_BLOCK_INSPECTOR': 'tests.test_spidermiddleware_block_inspector.inspect_block',
            'HTTPPROXY_SM_RECYCLE_REQUEST': 'scrapy_proxy_management.utils.recycle_request'
        })

        self.spider = Spider.from_crawler(crawler, name='foo')
        self.mw = BlockInspectorMiddleware.from_crawler(crawler)

    def test_process_spider_input(self):
        self.assertEqual(
            None,
            self.mw.process_spider_input(self.res_succeed, self.spider))

        self.assertRaises(
            ProxyBlockException,
            self.mw.process_spider_input, self.res_block, self.spider
        )

    def test_process_spider_exception(self):
        result = self.mw.process_spider_exception(
            self.res_block, ProxyBlockException(self.res_block), self.spider
        )

        for req, req_after_exception in zip(
                [self.req.replace(
                    dont_filter=True,
                    priority=self.mw.settings.getint('RETRY_PRIORITY_ADJUST')
                )],
                result
        ):
            _req = deepcopy(req)
            _req._meta = {}
            self.assertEqual(_req.__dict__, req_after_exception.__dict__)

        self.assertEqual(None, self.mw.process_spider_exception(
            self.res_block, OtherException(self.res_block), self.spider))
