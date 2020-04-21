# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json
import random
import re
import time
import traceback
from selenium import webdriver
from PIL import Image
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException, TimeoutException

import requests
from scrapy import signals, Request, FormRequest
from scrapy.http import HtmlResponse, Response
from scrapy.downloadermiddlewares.retry import RetryMiddleware

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
                print("代理" + proxy + "被网站封了")
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
        ua = random.choice(USER_AGENT_LIST)
        if ua:
            request.headers.setdefault('User-Agent', ua)


class FangDownloaderMiddleware(object):
    headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15",
    }

    # 处理response
    def process_response(self, request, response, spider):
        try:
            # 如果返回的url中包含“captcha”，则运行此程序
            if ('captcha' in response.url):
                # 记录原始的回调函数
                callback = request.callback
                # 用requests发起一次请求，获取cookies内的captcha_uid
                r = requests.get(response.url, headers=self.headers)
                self.cookies = requests.utils.dict_from_cookiejar(r.cookies)
                # 用requests下载验证码图片
                captcha_img_url = response.url.split('?t')[0] + 'captcha-image'
                captcha_data = self.get_captcha_data(captcha_img_url, captcha_img_url.split('-')[1].split('/')[0])
                # 获取token值，仅需加上referer
                cdnversion = re.search('cdnversion=(.*?)"', response.text).group(1)
                token = self.get_token(response.url, cdnversion)
                captcha_data.update({'token': str(token)})
                # 用scrapy的FormRequest构建request对象
                request = FormRequest(response.url, formdata=captcha_data, callback=callback, dont_filter=True)
                # 将cookies添加到request对象
                request.cookies = self.cookies
                requests.headers = {b'Host': b'search.fang.com'}
                # 返回request
                return request
            # 如果返回的url中不包含“captcha”，则直接返回response
            else:
                print("ok" * 20)
                return response
        except:
            traceback.print_exc()
            return response

    # 获取token
    def get_token(self, url, cdnversion):
        # captcha
        headers = {
            "Referer": url
        }
        captcha_url = url.split('?t')[0] + 'captcha.js?cdnversion=' + cdnversion
        r = requests.get(captcha_url, headers=headers)
        t2 = re.search("var t2 = (.*?);", r.text).group(1)
        return eval(t2)

    # 用requests下载验证码图片
    def get_captcha_data(self, url, name):
        r = requests.get(url, headers=self.headers, cookies=self.cookies)
        # 保存验证码图片
        image_name = str(int(time.time() * 1000))
        image_path = './captcha_image/' + image_name + '.png'
        with open(image_path, 'wb') as file:
            file.write(r.content)

        r = requests.post('http://127.0.0.1:7788', data=open(image_path, 'rb'))
        code = json.loads(r.text)['code']
        # 构建formdata，其中token不知道是个什么值，我就用随机数代替了
        captcha_data = {
            'code': code,
            'submit': '提交',
        }
        # 返回formdata
        return captcha_data



class ChromeDownloaderMiddleware(object):
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 设置无界面
        self.driver = webdriver.Chrome(executable_path='D://chromedriver_76.exe', options=options)
        self.driver.implicitly_wait(5)

    def process_response(self, request, response, spider):
        if "captcha" in request.url and ("访问验证" in response.text or "跳转" in response.text):
            self.driver.get(request.url)  # 获取网页链接内容
            while True:
                try:
                    self.driver.save_screenshot('bdbutton.png')
                    element = self.driver.find_element_by_xpath('//div[@class="image"]/img')  # 找到验证码图片
                    print(element.location)  # 打印元素坐标
                    print(element.size)  # 打印元素大小
                    left = element.location['x']
                    top = element.location['y']
                    right = element.location['x'] + element.size['width']
                    bottom = element.location['y'] + element.size['height']
                    im = Image.open('bdbutton.png')
                    im = im.crop((left, top, right, bottom))
                    image_name = str(int(time.time() * 1000))
                    image_path = './captcha_image/' + image_name + '.png'
                    im.save(image_path)
                    r = requests.post('http://127.0.0.1:7788', data=open(image_path, 'rb'))
                    code = json.loads(r.text)['code']
                    code_input = self.driver.find_element_by_id("code")
                    code_input.send_keys(code)
                    self.driver.find_element_by_xpath('//div[@class="button"]/input').click()
                    if '访问验证' not in self.driver.title:
                        break
                except NoSuchElementException:
                    break
                except TimeoutException:
                    continue
                except Exception:
                    traceback.print_exc()
                    continue
            response = HtmlResponse(url=request.url, body=self.driver.page_source, request=request,
                                    encoding='utf-8', status=200)  # 返回HTML数据
            return response
        else:
            return response

    def __del__(self):
        self.driver.close()


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
