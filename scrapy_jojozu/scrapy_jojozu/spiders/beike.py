#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 11:43
# @Author  : zjz
import threading
import time
import traceback
from urllib.parse import urlparse

import scrapy
from scrapy import Selector

from scrapy_jojozu.items import ScrapyJojozuItem
from scrapy_jojozu.util import AreaPosition

city_url = {
        '深圳': [
            "https://sz.zu.ke.com/zufang/pg0rcol1"
               ],
        "广州": [
            "https://gz.zu.ke.com/zufang/pg0rcol1"
        ],
        "上海": [
            "https://sh.zu.ke.com/zufang/pg0rcol1"
        ],
        "北京": [
            "https://bj.zu.ke.com/zufang/pg0rcol1"
        ]
}


class BeikeSpider(scrapy.Spider):
    """
    需要调用百度地图识别地域，添加线程锁来满足qps<=2
    """
    name = 'beike'
    allowed_domains = ['sz.zu.ke.com', 'gz.zu.ke.com', 'sh.zu.ke.com', 'bj.zu.ke.com']
    url = 'https://sz.zu.ke.com/zufang/pg{}rcol1'
    a = AreaPosition()
    lock = threading.Lock()

    start_urls = city_url.get('深圳') + city_url.get('广州') + city_url.get('上海') + city_url.get('北京')

    # def start_requests(self):
    #     for i in range(1,11):
    #         start_url = self.url.format(str(i))
    #         yield scrapy.Request(start_url)

    def parse(self, response):
        selector = Selector(response)
        rows = selector.xpath('//p[@class="content__list--item--title twoline"]/a/@href').extract()
        for row in rows:
            url = "https://sz.zu.ke.com" + row
            yield scrapy.Request(url, meta={
                'dont_redirect': True,
                'handle_httpstatus_list': [302],
                'list_url': response.url
            }, callback=self.parse_item)

    def parse_item(self, response):
        try:
            self.lock.acquire()
            item = ScrapyJojozuItem()
            item["title"] = response.xpath('//p[@class="content__title"]/text()').extract_first()
            item['lease'] = response.xpath('//ul[@class="content__aside__list"]/li[1]/text()').extract_first(default="")
            item['type'] = response.xpath('//ul[@class="content__aside__list"]/li[2]/text()').extract_first().split(' ')[0]
            item['image'] = response.xpath('//ul[@class="content__article__slide--small content__article__slide_dot"]//img/@src').extract()
            item['payment_method'] = response.xpath(
                '//ul[@class="table_row"]//li[1]/text()').extract_first()
            item['cost'] = response.xpath(
                '//ul[@class="table_row"]//li[2]/text()').extract_first()
            item['cash_pledge'] = response.xpath(
                '//ul[@class="table_row"]//li[3]/text()').extract_first()
            address = item["title"].split(' ')[0].split('·')[-1]
            # city 需根据列表页传meta进来
            if 'sz' in urlparse(response.url)[1]:
                item['city'] = '深圳'
            elif 'gz' in urlparse(response.url)[1]:
                item['city'] = '广州'
            elif 'sh' in urlparse(response.url)[1]:
                item['city'] = '上海'
            elif 'bj' in urlparse(response.url)[1]:
                item['city'] = '北京'

            location = self.a.get_geocoder(address, item['city'])
            item['area'] = self.a.get_area(location, item['city'])
            item['location'] = self.a.get_place(location, item['city'])

            item['had_agent'] = 1
            item['service_charge'] = response.xpath(
                '//ul[@class="table_row"]//li[4]/text()').extract_first()
            item['agent_cost'] = response.xpath(
                '//ul[@class="table_row"]//li[5]/text()').extract_first()

            item['support'] = [i.strip() for i in response.xpath(
                '//ul[@class="content__article__info2"]/li[@class="fl oneline  "]/text()').extract() if i.strip()]
            item['description'] = ''.join(
                response.xpath('//div[@class="content__article__info"]/ul[1]//text()').extract()).replace(" ", "").replace(" ","").replace("\n\n","\n")
            item['update_time'] = response.xpath('//div[@class="content__subtitle"]').re("\d+-\d+-\d+")[0]
            timeArray = time.strptime(item['update_time'], '%Y-%m-%d')
            timestamp = int(time.mktime(timeArray))
            item['update_timestamp'] = timestamp
            item['url'] = response.url
            item['source'] = "贝壳"
        except Exception as e:
            traceback.print_exc()
        finally:
            self.lock.release()
        yield item