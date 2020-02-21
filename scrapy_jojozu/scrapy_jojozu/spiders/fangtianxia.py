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

from scrapy_jojozu.scrapy_jojozu.util import time_standard
from ..items import ScrapyJojozuItem

#https://callback.58.com/antibot/verifycode?serialId=c779e6a2c00fdce7a6cee6f668175e91_fcaef7d7ca234ab283a97bcd5c8b3b2e&code=21&sign=6ac3d1fec452b88acdd2bfdf8e6e67e6&namespace=anjuke_zufang_detail_pc&url=https%3A%2F%2Fsz.zu.anjuke.com%2Ffangyuan%2F1274453653824521%3Fisauction%3D1%26shangquan_id%3D1846
city_url = {
        '深圳': [
            "https://sz.zu.fang.com"
            #    "http://search.fang.com/captcha-039b1eac8d00463825/redirect?h=https://sz.zu.fang.com/house/i3%s/?_rfss=2a&rfss=2-45871c4c2fc9bd3ea9-2a"
               ],
        # "广州": [
        #     "https://gz.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        # ],
        # "上海": [
        #     "https://sh.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        # ],
        # "北京": [
        #     "https://bj.zu.anjuke.com/?kw=%E4%B8%AA%E4%BA%BA%E6%88%BF%E6%BA%90&utm_term=%E5%85%8D%E4%B8%AD%E4%BB%8B%E8%B4%B9%E7%A7%9F%E6%88%BF"
        # ]
}

class FangSpider(Spider):
    name = 'fantianxia'
    allowed_domains = ['sz.zu.fang.com', "search.fang.com"]
    handle_httpstatus_list = [404, 500]
    lock = threading.Lock()
    start_urls = city_url.get('深圳')

    custom_settings = {
        'DOWNLOAD_DELAY': 0.2,
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
                page_url = response.url + '/i3' + str(i) + '/'
                yield scrapy.Request(page_url, callback=self.parse_page, meta={'main_url': response.meta.get('main_url')})

    def parse_page(self, response):
        row_list = response.xpath('//dd[@class="info rel"]')
        for row in row_list:
            next_url = response.meta.get('main_url') + row.xpath('p[@class="title"]/a/@href').extract_first()
            yield scrapy.Request(next_url, callback=self.item_parse)

    # def do_captcha(self, ):

    def item_parse(self, response):
        item = ScrapyJojozuItem()
        item["title"] = response.xpath('//div[@class="title"]/text()').extract_first().replace(" ", "").replace(" ","").replace("\n","").replace("\r", "")
        # 租赁方式
        item["lease"] = response.xpath('//div[@class="tt"]/text()').extract()[0]
        # 户型
        item["type"] = response.xpath('//div[@class="tt"]/text()').extract()[1]
        # 图片为ArrayList
        item["image"] = [i if 'http:' in i else 'http:' + i for i in response.xpath('//div[@class="cont-sty1 clearfix"]//img/@src').extract()]
        # 付款方式
        item["payment_method"] = "unknown"
        # 月租金
        item["cost"] = response.xpath('//div[@class="trl-item sty1"]/i/text()').extract_first()
        # 押金
        item["cash_pledge"] = "unknown"
        # 区域
        item["area"] = response.xpath('//div[@class="rcont"]/a/text()').extract()[0]
        # 是否有中介
        item["had_agent"] = 1
        # 服务费
        item["service_charge"] = "unknown"
        # 中介费
        item["agent_cost"] = "unknown"
        # 最近地铁站
        item["location"] =  response.xpath('//div[@class="rcont"]/a/text()').extract()[3]
        # 设施
        item["support"] =  re.search("var peitao = '(.*?)';", response.text).group(1)
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
        print(item)

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
            item['update_time'] = soup.find('div', attrs={'class': "right-info"}).find('b').text
            timeArray = time.strptime(item['update_time'], '%Y年%m月%d日')
            timestamp = int(time.mktime(timeArray))
            item['update_timestamp'] = timestamp
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
