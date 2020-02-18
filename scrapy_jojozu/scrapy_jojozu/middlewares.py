# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json
import random

import requests
from scrapy import signals

from scrapy_jojozu.settings import PROXIES, USER_AGENT_LIST

"""
代理中间件，scrapy底层使用urllib的请求，所以要补齐协议，尽量请求主站域名
"""

def get_proxy():
    res = requests.get("http://127.0.0.1:3289/pop")
    result = json.loads(res.text)
    return result

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        # proxy = random.choice(PROXIES)
        if request.meta.get("proxy"):
            return
        # proxy = get_proxy()
        proxy = random.choice(PROXIES)
        ua = random.choice(USER_AGENT_LIST)
        headers = {
            "User-Agent": ua
        }
        try:
            if spider.name == "lianjia":
                main_url = "https://sz.lianjia.com/"
            elif spider.name == "anjuke":
                main_url = "https://sz.zu.anjuke.com"
            elif spider.name == "douban":
                main_url = "https://www.douban.com"
            elif spider.name == "fantianxia":
                main_url = "https://sz.fang.com"
                request.headers.setdefault('Host', "sz.zu.fang.com")
            else:
                main_url = "https://www.baidu.com"
            res = requests.get(main_url,
                                   proxies={"http": "http://" + proxy, "https": "https://" + proxy},
                                   # proxies=proxy,
                                   headers=headers,
                                   timeout=5)
            if res.status_code == 200:
                request.meta['proxy'] = "http://" + proxy
                # request.meta['proxy'] = proxy.get('http') or proxy.get('https')
                return
            else:
                print("代理"+proxy+"被网站封了")
                # print("代理" + (proxy.get('http') or proxy.get('https')) + "被网站封了")
                self.process_request(request, spider)
        except (requests.exceptions.ProxyError, requests.exceptions.ReadTimeout):
            print("代理" + proxy + "暂时无法使用")
            # print("代理" + (proxy.get('http') or proxy.get('https')) + "暂时无法使用")
            self.process_request(request, spider)

    def process_exception(self, request, exception, spider):
        proxy = random.choice(PROXIES)
        request.meta['proxy'] = "https://" + proxy


"""
UA中间件，随机切换UA
settings中要注释原本的UA中间件
'scrapy.contrib.downloadermiddleware.useragent.UserAgentMiddleware': None,
"""


class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        if spider.name == "fantianxia":
            # request.meta['proxy'] = "http://127.0.0.1:8889"
            if 'rfss' in request.url:
                request.headers.update(
                    {'Host': 'sz.zu.fang.com', 'Connection': 'keep-alive', 'Upgrade-Insecure-Requests': '1',
                     'User-Agent': 'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/79.0.3945.88Safari/537.36',
                     'Sec-Fetch-User': '?1',
                     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                     'Sec-Fetch-Site': 'none', 'Sec-Fetch-Mode': 'navigate', 'Accept-Encoding': 'gzip,deflate,br',
                     'Accept-Language': 'zh-CN,zh;q=0.9'})
                if 'referer' in request.headers.to_unicode_dict().keys():
                    request.headers.pop('Referer')
                if 'cookie' in request.headers.to_unicode_dict().keys():
                    request.headers.pop('Cookie')
        else:
            ua = random.choice(USER_AGENT_LIST)
            if ua:
                request.headers.setdefault('User-Agent', ua)



class ScrapyJojozuSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyJojozuDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
