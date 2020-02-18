#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/27 11:42
# @Author  : zjz


# import os
# import sys
#
# sys.path.append("../")  # 解决潜在的路径依赖问题
# sys.path.append("../../")  # 解决潜在的路径依赖问题
# sys.path.append("../../../")  # 解决潜在的路径依赖问题
# sys.path.append("../../../../")  # 解决潜在的路径依赖问题
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# print(os.path.dirname(os.path.abspath(__file__)))
# from scrapy.cmdline import execute
# # 添加当前项目的绝对地址
#
# # 执行 scrapy 内置的函数方法execute，  使用 crawl 爬取并调试
#
# execute(['scrapy', 'crawl', 'douban'])


from scrapy.utils.log import configure_logging
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy_jojozu.spiders.douban import DoubanSpider

def crawl_job():
    settings = get_project_settings()
    runner = CrawlerRunner(settings)
    return runner.crawl(DoubanSpider)

def schedule_next_crawl(null, sleep_time):
    reactor.callLater(sleep_time, crawl)

def crawl():
    configure_logging({'LOG_FORMAT': '%(levelname)s: %(message)s'})
    d = crawl_job()
    # 设置爬取频率
    d.addCallback(schedule_next_crawl, 10)
    d.addErrback(catch_error)

def catch_error(failure):
    print(failure.value)

if __name__ == "__main__":
    crawl()
    reactor.run()