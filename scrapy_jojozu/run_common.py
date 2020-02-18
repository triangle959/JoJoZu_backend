#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/9 10:46
# @Author  : zjz

# from scrapy.utils.log import configure_logging
# from twisted.internet import reactor, defer
# from scrapy.crawler import CrawlerRunner
# from scrapy.utils.project import get_project_settings
# from scrapy_jojozu.spiders.anjuke import AnjukeSpider
# from scrapy_jojozu.spiders.beike import BeikeSpider
# from scrapy_jojozu.spiders.lianjia import LianjiaSpider
#
# configure_logging()
# settings = get_project_settings()
# runner = CrawlerRunner(settings)
#
#
# @defer.inlineCallbacks
# def crawl():
#     yield runner.crawl(AnjukeSpider)
#     yield runner.crawl(BeikeSpider)
#     yield runner.crawl(LianjiaSpider)
#     reactor.stop()
#
# crawl()
# reactor.run() # the script will block here until the last crawl call is finished


from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from apscheduler.schedulers.twisted import TwistedScheduler

from scrapy_jojozu.spiders.anjuke import AnjukeSpider
from scrapy_jojozu.spiders.beike import BeikeSpider
from scrapy_jojozu.spiders.lianjia import LianjiaSpider
from scrapy_jojozu.spiders.douban import DoubanSpider

process = CrawlerProcess(get_project_settings())
scheduler = TwistedScheduler()
scheduler.add_job(process.crawl, 'interval', args=[AnjukeSpider], minutes=30),
scheduler.add_job(process.crawl, 'interval', args=[BeikeSpider], minutes=30),
scheduler.add_job(process.crawl, 'interval', args=[LianjiaSpider], minutes=30),
scheduler.add_job(process.crawl, "interval", args=[DoubanSpider], minutes=30)
scheduler.start()
process.start(False)

