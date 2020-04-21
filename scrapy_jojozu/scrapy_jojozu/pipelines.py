# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import traceback

import pymongo
import pymysql

from scrapy_jojozu.items import ScrapyJojozuItem
from scrapy_jojozu.dbconfig import dbparams, mongo_url

class MysqlPipeline(object):
    def __init__(self):
        self.conn = pymysql.connect(**dbparams)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        self.reConnect()
        if isinstance(item, ScrapyJojozuItem):
            insert_sql = "INSERT INTO `jojozu`.`shenzhen` (title,lease,type,image,payment_method,area,location,support,description,update_time,url,source,cost,cash_pledge,had_agent,service_charge,agent_cost) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            self.cursor.execute(insert_sql, (item['title'], item['lease'], item['type'], item['image'], item['payment_method'],
                item['area'], item['location'], item['support'], item['description'], item['update_time'], item['url'],
                item['source'], item['cost'], item['cash_pledge'], item['had_agent'],
                item['service_charge'], item['agent_cost']
            ))
            try:
                self.conn.commit()
                print(item['title'] + "成功保存Mysql数据库")
            except:
                self.conn.rollback()
                print(item['title'] + '保存失败')

            return item

    def reConnect(self):
        try:
            self.conn.ping()
        except:
            self.conn = pymysql.connect(**dbparams)

    def close_spider(self, spider):
        self.cursor.close()
        self.conn.close()


class MongoPipeline(object):
    def __init__(self):
        self.conn = pymongo.MongoClient(mongo_url)
        self.db = self.conn['JoJoZu']

    def process_item(self, item, spider):
        try:
            if spider.name == 'douban':
                collection = self.db['douban']
                source = "豆瓣"
            else:
                collection = self.db['common']
                source = item["source"]
            if collection.insert(dict(item)):
                print(item["title"] + source + "插入成功！")
        except UnicodeEncodeError:
            print("豆瓣标题出现无法gbk解码字符")
        except pymongo.errors.DuplicateKeyError:
            print(item["title"] + source + "重复，抛弃")
        except Exception:
            traceback.print_exc()
            print(item["title"] + source + "出现上述错误")


    def close_spider(self, spider):
        self.conn.close()