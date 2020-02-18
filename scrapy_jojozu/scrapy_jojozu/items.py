# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Join

class ScrapyJojozuItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    # 租赁方式
    lease = scrapy.Field()
    # 户型
    type = scrapy.Field()
    # 图片为ArrayList
    image = scrapy.Field()
    # 付款方式
    payment_method = scrapy.Field()
    # 月租金
    cost = scrapy.Field()
    # 押金
    cash_pledge = scrapy.Field()
    # 区域
    area = scrapy.Field()
    # 是否有中介
    had_agent = scrapy.Field()
    # 服务费
    service_charge = scrapy.Field()
    # 中介费
    agent_cost = scrapy.Field()
    # 最近地铁站
    location = scrapy.Field()
    # 设施
    support = scrapy.Field()
    description = scrapy.Field()
    # 更新时间以及更新时间戳
    update_time = scrapy.Field()
    update_timestamp = scrapy.Field()
    url = scrapy.Field()
    # 来源渠道
    source = scrapy.Field()
    city = scrapy.Field()


class DoubanItem(scrapy.Item):
    # 标题
    title = scrapy.Field()
    # 发布者
    author = scrapy.Field()
    # 内容H5
    content = scrapy.Field()
    # 图片 ArrayList
    image = scrapy.Field()
    # 回应数
    replay_num = scrapy.Field()
    # 创建时间
    create_time = scrapy.Field()
    # 更新时间
    update_time = scrapy.Field()
    update_timestamp = scrapy.Field()
    # 链接
    url = scrapy.Field()
    city = scrapy.Field()