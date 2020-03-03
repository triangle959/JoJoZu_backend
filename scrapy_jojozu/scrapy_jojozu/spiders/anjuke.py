#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/7 17:46
# @Author  : zjz
import base64
import re
import threading
import time
import traceback

from bs4 import BeautifulSoup
import os
from scrapy import Spider, Selector
import scrapy
from urllib.parse import urlparse
from fontTools.ttLib import TTFont
from scrapy_jojozu.items import ScrapyJojozuItem

#https://callback.58.com/antibot/verifycode?serialId=c779e6a2c00fdce7a6cee6f668175e91_fcaef7d7ca234ab283a97bcd5c8b3b2e&code=21&sign=6ac3d1fec452b88acdd2bfdf8e6e67e6&namespace=anjuke_zufang_detail_pc&url=https%3A%2F%2Fsz.zu.anjuke.com%2Ffangyuan%2F1274453653824521%3Fisauction%3D1%26shangquan_id%3D1846
from scrapy_jojozu.util import time_standard

city_url = {
        '深圳': [
            "https://sz.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
               ],
        "广州": [
            "https://gz.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        ],
        "上海": [
            "https://sh.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        ],
        "北京": [
            "https://bj.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        ]
}

class AnjukeSpider(Spider):
    name = 'anjuke'
    allowed_domains = ['sz.zu.anjuke.com', 'gz.zu.anjuke.com', "sh.zu.anjuke.com", "bj.zu.anjuke.com"]
    lock = threading.Lock()
    start_urls = city_url.get('深圳') + city_url.get('广州') + city_url.get('上海') + city_url.get('北京')

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'lxml')
        selector = Selector(response)
        href_list = selector.xpath('//div[@class="zu-info"]/h3/a/@href').extract()
        for href in href_list:
            yield scrapy.Request(href, meta={
                'dont_redirect': True,
                'handle_httpstatus_list': [302],
                'list_url': response.url
            }, callback=self.parse_item)

    # 遇到重定向到验证码页面的处理逻辑如下：
    # 禁止跳转，允许302状态码，在回调函数中进行判断状态码302，直接return掉。缺点：无法进行重试该任务
    def parse_item(self, response):
        if response.status == 302:
            return
        try:
            print('开始加锁')
            self.lock.acquire()
            font_src = re.search("src:url\('(.*?)'\)", response.text).group(1)
            font_face = font_src.split("base64,")
            # 字体文件生成，每个页面返回的字体文件都不同，需要持续更新
            if 'ttf' in font_face[0] or 'woff' in font_face[0]:
                b = base64.b64decode(font_face[1])
                with open('anjuke.ttf', 'wb')as f:
                    f.write(b)
            font = TTFont('anjuke.ttf')
            font.saveXML('anjuke.xml')
            # 如果有 cmap 可以拿到替换数字的unicode码，再通过正则匹配到该unicode码进行替换
            cmap = font['cmap'].getBestCmap()
            mapdict = {}
            for i in cmap:
                pat = re.compile(r'(\d+)')
                values = int(re.search(pat, cmap[i])[1]) - 1
                keys = hex(i)
                new_keys = '&#x' + keys[2:] + ';'
                mapdict[new_keys] = values
            print(mapdict)
            right_html = response.text
            for k, v in mapdict.items():
                right_html = right_html.replace(k, str(v))
            soup = BeautifulSoup(right_html, 'lxml')
            item = ScrapyJojozuItem()
            item['title'] = soup.find('h3', attrs={'class': 'house-title'}).text.replace('\n', "")
            item['type'] = \
            soup.find('div', attrs={'class': 'title-basic-info'}).find_all('span', attrs={'class': 'info-tag'})[
                1].get_text().replace('\n', "").replace(' ', "")
            item['lease'] = soup.find('div', attrs={'class': 'title-basic-info'}).find('li', attrs={'class': 'rent'}).text
            item['image'] = [i.get('data-src') for i in
                             soup.find('div', id="room_pic_wrap", attrs={'class': 'switch_list'}).find_all('img')]
            item['payment_method'] = soup.find('li', attrs={'class': 'full-line'}).find('span',
                                                                                        attrs={'class': 'type'}).text
            item['cost'] = soup.find('li', attrs={'class': 'full-line'}).find('span', attrs={'class': 'price'}).text
            # item['cash_pledge'] = soup.find('li', attrs={'class':'full-line'}).find('span',attrs={'class':'price'}).text
            item['cash_pledge'] = item['payment_method']
            try:
                item['area'] = soup.find_all('a', class_='link',attrs={'target': True})[0].text
            except:
                print(response.url)
            item['had_agent'] = 1
            item['service_charge'] = "服务费未知"
            item['agent_cost'] = "中介费未知"
            item['location'] = ",".join([i.text for i in soup.find_all('a', class_='link',attrs={'target': True})[1:]])
            item['support'] = [i.find('div').text for i in
                               soup.find_all('li', attrs={'class': re.compile('peitao-item(.*)has')})]
            item['description'] = soup.find('div', attrs={'class': 'auto-general'}).text
            item['update_time'],item['update_timestamp'] = time_standard(soup.find('div', attrs={'class': "right-info"}).find('b').text)
            item['url'] = response.url
            item['source'] = "安居客"
            if 'sz' in urlparse(response.url)[1]:
                item['city'] = '深圳'
            elif 'gz' in urlparse(response.url)[1]:
                item['city'] = '广州'
            elif 'sh' in urlparse(response.url)[1]:
                item['city'] = '上海'
            elif 'bj' in urlparse(response.url)[1]:
                item['city'] = '北京'
        except Exception as e:
            traceback.print_exc()
        finally:
            print("释放锁")
            self.lock.release()
            yield item
