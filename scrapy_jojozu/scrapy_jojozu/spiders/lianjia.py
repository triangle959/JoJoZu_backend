# -*- coding: utf-8 -*-
import threading
import time
import traceback

import scrapy
from scrapy.selector import Selector
from urllib.parse import urlparse
from scrapy_jojozu.items import ScrapyJojozuItem
from scrapy_jojozu.util import AreaPosition

city_url = {
        '深圳': [
            "https://sz.lianjia.com/zufang/pg0rco11"
               ],
        "广州": [
            "https://gz.lianjia.com/zufang/pg0rco11"
        ],
        "上海": [
            "https://sh.lianjia.com/zufang/pg0rco11"
        ],
        "北京": [
            "https://bj.lianjia.com/zufang/pg0rco11"
        ]
}


class LianjiaSpider(scrapy.Spider):
    name = 'lianjia'
    allowed_domains = ['sz.lianjia.com', 'gz.lianjia.com', 'sh.lianjia.com', 'bj.lianjia.com']

    url = 'https://sz.lianjia.com/zufang/pg{}rco11'
    a = AreaPosition()
    lock = threading.Lock()

    start_urls = city_url.get('深圳') + city_url.get('广州') + city_url.get('上海') + city_url.get('北京')
    # def start_requests(self):
    #     for i in range(1,11):
    #         start_url = self.url.format(str(i))
    #         yield scrapy.Request(start_url)

    def parse(self, response):
        selector = Selector(response)
        href_list = selector.xpath('//a[@class="content__list--item--aside"]/@href').extract()
        for href in href_list:
            if 'apartment' not in href:
                next_url = urlparse(response.url)[0] + '://' + urlparse(response.url)[1] + href
                yield scrapy.Request(next_url,  meta={
                    'dont_redirect': True,
                    'handle_httpstatus_list': [302],
                    'list_url': response.url
                }, callback=self.parse_item)

    def parse_item(self, response):
        try:
            self.lock.acquire()
            selector = Selector(response)
            item = ScrapyJojozuItem()
            item['title'] = selector.xpath('//p[@class="content__title"]/text()').extract_first()
            item['lease'] = response.xpath('//ul[@class="content__aside__list"]/li[1]/text()').extract_first(default="")
            try:
                # 如果跳到公寓页面则跳过此url
                item['type'] = response.xpath('//ul[@class="content__aside__list"]/li[2]/text()').extract_first().split(' ')[0]
            except:
                return
            item['image'] = selector.xpath('//div[@class="content__thumb--box"]//img/@src').extract()
            item['payment_method'] = selector.xpath(
                '//div[@class="content__article__info3 cost_box"]//div[@class="table_content"]//li[1]/text()').extract_first(
                default="")
            item['cost'] = selector.xpath(
                '//div[@class="content__article__info3 cost_box"]//div[@class="table_content"]//li[2]/text()').extract_first(
                default="")
            item['cash_pledge'] = selector.xpath(
                '//div[@class="content__article__info3 cost_box"]//div[@class="table_content"]//li[3]/text()').extract_first(
                default="")
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
            item['service_charge'] = selector.xpath(
                '//div[@class="content__article__info3 cost_box"]//div[@class="table_content"]//li[4]/text()').extract_first(
                default="")
            item['agent_cost'] = selector.xpath(
                '//div[@class="content__article__info3 cost_box"]//div[@class="table_content"]//li[5]/text()').extract_first(
                default="")
            item['support'] = [i.strip() for i in selector.xpath(
                '//ul[@class="content__article__info2"]/li[@class="fl oneline  "]/text()').extract() if i.strip()]
            item['description'] = ''.join(
                selector.xpath('//div[@class="content__article__info"]/ul[1]//text()').extract()).replace(" ", "").replace(" ","").replace("\n\n","\n")
            item['update_time'] = selector.xpath('//div[@class="content__subtitle"]').re("\d+-\d+-\d+")[0]
            timeArray = time.strptime(item['update_time'], '%Y-%m-%d')
            timestamp = int(time.mktime(timeArray))
            item['update_timestamp'] = timestamp
            item['url'] = response.url
            item['source'] = "链家"
        except Exception as e:
            traceback.print_exc()
        finally:
            self.lock.release()
        yield item
