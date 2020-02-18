#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/27 11:36
# @Author  : zjz
import time

import scrapy
from scrapy.selector import Selector
from bs4 import BeautifulSoup

from scrapy_jojozu.items import DoubanItem

city_url = {
    '深圳': ['https://www.douban.com/group/106955/',  # 深圳租房团
           'https://www.douban.com/group/szsh/',  # 深圳租房
           'https://www.douban.com/group/nanshanzufang/',  # 深圳租房-南山租房|深圳南山租房
           'https://www.douban.com/group/futianzufang/',  # 深圳租房-福田租房|深圳福田租房
           'https://www.douban.com/group/637638/',  # 深圳租房
           'https://www.douban.com/group/baoanzufang/',  # 深圳租房-宝安租房|深圳宝安租房
           'https://www.douban.com/group/637700/',  # 深圳租房@福田租房
           'https://www.douban.com/group/nanshanzufang/',  # 深圳租房★南山租房★个人免费推广
           ],
    "广州": [
        'https://www.douban.com/group/gz020/',      # 广州租房
        'https://www.douban.com/group/gz_rent/',    # 广州租房
        'https://www.douban.com/group/tianhezufang/',   # 广州租房-天河租房|广州天河租房
        'https://www.douban.com/group/637323/',     # 广州租房-天河租房★广州天河租房
    ],
    "上海": [
        'https://www.douban.com/group/shanghaizufang/',     # 上海租房
        'https://www.douban.com/group/homeatshanghai/',     # 上海租房---房子是租来的，生活不是
        'https://www.douban.com/group/pudongzufang/',        # 上海租房@浦东租房
        'https://www.douban.com/group/467799/',             # 上海租房@房东直租
        'https://www.douban.com/group/383972/',             # 上海合租族_魔都租房
    ],
    "北京": [
        'https://www.douban.com/group/beijingzufang/',      # 北京租房
        'https://www.douban.com/group/zhufang/',            # 北京无中介租房
        'https://www.douban.com/group/26926/',              # 北京租房豆瓣
        'https://www.douban.com/group/279962/',             # 北京租房（非中介）
    ]
}


class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['www.douban.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,
    }
    start_urls = city_url.get('深圳') + city_url.get('广州') + city_url.get('上海') + city_url.get('北京')

    def parse(self, response):
        selector = Selector(response)
        row_list = selector.xpath('//table[@class="olt"]//tr[@class=""]')
        for row in row_list:
            if row.xpath('td[@class="title"]/span'):
                continue
            next_url = row.xpath('td[@class="title"]/a/@href').extract_first()
            title = row.xpath('td[@class="title"]/a/@title').extract_first()
            replay_num = row.xpath('td[3]/text()').extract_first()
            update_time = row.xpath('td[4]/text()').extract_first()
            yield scrapy.Request(next_url, callback=self.parse_item, meta={
                "title": title, "replay_num": replay_num, "update_time": update_time, "list_url": response.url})

    def parse_item(self, response):
        selector = Selector(response)
        item = DoubanItem()
        item["url"] = response.url
        item["title"] = response.meta.get('title')
        item["author"] = selector.xpath('//h3/span[1]/a/text()').extract_first()
        item["content"] = selector.xpath('//div[@class="topic-richtext"]').extract_first()
        item["image"] = selector.xpath('//div[@class="topic-richtext"]//img/@src').extract()
        item["create_time"] = selector.xpath('//h3/span[2]/text()').extract_first()
        if item["create_time"].split('-')[1] > response.meta.get('update_time').split('-')[0]:
            item["update_time"] = str(int(item["create_time"].split('-')[0]) + 1) + '-' + response.meta.get(
                'update_time')
        else:
            item["update_time"] = item["create_time"].split('-')[0] + '-' + response.meta.get('update_time')
        item["replay_num"] = response.meta.get('replay_num')
        timeArray = time.strptime(item['update_time'], '%Y-%m-%d %H:%M')
        timestamp = int(time.mktime(timeArray))
        item["update_timestamp"] = timestamp
        for city_name, url_list in city_url.items():
            if response.meta.get('list_url') in url_list:
                item['city'] = city_name
                break
        yield item
