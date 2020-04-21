#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/1/2 17:46
# @Author  : zjz
import base64
import re
import threading
import time
import traceback
from bs4 import BeautifulSoup
from scrapy import Spider, Selector
import scrapy
from urllib.parse import urlparse, unquote_to_bytes
from fontTools.ttLib import TTFont

from scrapy_jojozu.util import time_standard
from scrapy_jojozu.items import ScrapyJojozuItem

#https://callback.58.com/antibot/verifycode?serialId=c779e6a2c00fdce7a6cee6f668175e91_fcaef7d7ca234ab283a97bcd5c8b3b2e&code=21&sign=6ac3d1fec452b88acdd2bfdf8e6e67e6&namespace=anjuke_zufang_detail_pc&url=https%3A%2F%2Fsz.zu.anjuke.com%2Ffangyuan%2F1274453653824521%3Fisauction%3D1%26shangquan_id%3D1846
city_url = {
        '深圳': [
            "https://sz.zu.fang.com"
            #    "http://search.fang.com/captcha-039b1eac8d00463825/redirect?h=https://sz.zu.fang.com/house/i3%s/?_rfss=2a&rfss=2-45871c4c2fc9bd3ea9-2a"
               ],
        "广州": [
            "https://gz.zu.fang.com"
        ],
        "上海": [
            "https://sh.zu.fang.com"
        ],
        "北京": [
            "https://zu.fang.com"
        ]
}

class FangSpider(Spider):
    name = 'fantianxia'
    allowed_domains = ['sz.zu.fang.com', 'gz.zu.fang.com', 'sh.zu.fang.com', 'zu.fang.com', "search.fang.com"]
    lock = threading.Lock()
    start_urls = city_url.get('深圳')

    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,
        "HTTPERROR_ALLOWED_CODES": [404],
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODECS": [500, 502, 503, 504, 408, 404],
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy_jojozu.middlewares.ChromeDownloaderMiddleware': 543,
        }
    }

    def start_requests(self):
        for city_main_url in city_url.values():
            for url in city_main_url:
                yield scrapy.Request(url)

    def parse(self, response):
        area_list = response.xpath('//dl[@id="rentid_D04_01"]/dd/a[position()>1]/@href').extract()
        for area in area_list:
            area_url = response.url + area
            yield scrapy.Request(area_url, callback=self.parse_area, meta={'main_url': response.url})

    def parse_area(self, response):
        max_page = response.xpath('//div[@id="rentid_D10_01"]/span/text()').extract_first()
        if max_page:
            max_page_num = max_page[1:-1]
            for i in range(1,int(max_page_num)+1):
                page_url = response.url + 'i3' + str(i) + '/'
                yield scrapy.Request(page_url, callback=self.parse_page, meta={'main_url': response.meta.get('main_url')})

    def parse_page(self, response):
        row_list = response.xpath('//dd[@class="info rel"]')
        for row in row_list:
            next_url = response.meta.get('main_url') + row.xpath('p[@class="title"]/a/@href').extract_first()
            yield scrapy.Request(next_url, callback=self.item_parse, dont_filter=True)

    # def do_captcha(self, ):

    def item_parse(self, response):
        print("inter item_parse")
        item = ScrapyJojozuItem()
        item["title"] = response.xpath('//div[@class="title"]/text()').extract_first().replace(" ", "").replace(" ","").replace("\n","").replace("\r", "")
        # 租赁方式
        item["lease"] = response.xpath('//div[@class="tt"]/text()').extract()[0]
        # 户型
        item["type"] = response.xpath('//div[@class="tt"]/text()').extract()[1]
        # 图片为ArrayList
        item["image"] = [i if 'http:' in i else 'http:' + i for i in response.xpath('//div[@class="cont-sty1 clearfix"]//img/@src').extract()]
        # 付款方式
        item["payment_method"] = response.xpath('//div[@class="trl-item sty1"]/text()').extract_first().replace('元/月', "").replace('（',"").replace('）',"")
        # 月租金
        item["cost"] = int(response.xpath('//div[@class="trl-item sty1"]/i/text()').extract_first())
        # 押金
        item["cash_pledge"] = response.xpath('//div[@class="trl-item sty1"]/text()').extract_first().replace('元/月', "").replace('（',"").replace('）',"")
        # 区域
        item["area"] = response.xpath('//div[@class="rcont"]/a/text()').extract()[0]
        # 是否有中介
        item["had_agent"] = 1
        # 服务费
        item["service_charge"] = "服务费未知"
        # 中介费
        item["agent_cost"] = "中介费未知"
        # 最近地铁站
        location = response.xpath('//div[@class="rcont"]/a/text()')
        item["location"] =  location.re('线(.*?)站')[0] if location.re('线(.*?)站') else location.extract_first()
        # 设施
        item["support"] = re.search("var peitao = '(.*?)';", response.text).group(1)
        item["description"] = response.xpath('//li[@class="font14 fyld"]/div[@class="fyms_con floatl gray3"]').xpath('string(.)').extract_first()
        # 更新时间以及更新时间戳
        item['update_time'],item['update_timestamp'] = time_standard(response.xpath('//div[@class="gray9 fybh-zf"]/span[2]/text()').extract_first().replace("更新时间", "").replace(" ", ""))

        item["url"] = response.url
        # 来源渠道
        item["source"] = "房天下"
        if 'sz' in urlparse(response.url)[1]:
            item['city'] = '深圳'
        elif 'gz' in urlparse(response.url)[1]:
            item['city'] = '广州'
        elif 'sh' in urlparse(response.url)[1]:
            item['city'] = '上海'
        elif 'bj' in urlparse(response.url)[1]:
            item['city'] = '北京'
        yield item
