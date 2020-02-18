#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/4 11:33
# @Author  : zjz
import json

import requests



class AreaPosition:
    """
    通过调用百度api获取输入地点的附近的地铁站公交站
    """

    def __init__(self):
        self.ak = 'VdRqCmkKq3UZa9aOkuQO9sDpxhCmDxz9'

    def get_geocoder(self, address, city):
        url = 'http://api.map.baidu.com/geocoder?address={}&output=json&key={}&city={}'.format(address, self.ak, city)
        res = requests.get(url)
        res_json = json.loads(res.text)
        if res_json.get("status") == "OK":
            return res_json["result"].get("location")

    def get_place(self, location, city):
        """
        获取最近的交通设置，对应字段location
        :param location: 百度获取位置信息
        :param city: 搜索城市
        :return:
        """
        # location先纬度后经度
        url = "http://api.map.baidu.com/place/v2/search?query={}&location={},{}&page_size=2&page_num=0&scope=2&region={}&output=json&ak={}"
        # location = self.get_geocoder(address, city)
        url = url.format("地铁", location.get("lat"), location.get("lng"), city, self.ak)
        res = requests.get(url)
        res_json = json.loads(res.text)
        if res_json.get("status") == 0:
            result_list = res_json.get("results")
            result_list = sorted(result_list, key=lambda r : r["detail_info"]["distance"])
            return ",".join(i["name"] for i in result_list)

    def get_area(self, location, city):
        """
        获取最近区域 对应字段area
        :param location:
        :param city:
        :return:
        """
        url = "http://api.map.baidu.com/place/v2/search?query=%E5%8C%BA&location={},{}&page_size=1&page_num=0&scope=2&region={}&output=json&ak={}".format(location.get("lat"), location.get("lng"), city, self.ak)
        # location = self.get_geocoder(address, city)
        res = requests.get(url)
        res_json = json.loads(res.text)
        if res_json.get("status") == 0:
            result_list = res_json.get("results")
            return result_list[0].get("address")


if __name__ == '__main__':
    keyword = "万科蛇口公馆"
    city = "深圳"
    a = AreaPosition()
    location = a.get_geocoder(keyword,city)
    print(a.get_area(location, city))
    print(a.get_place(location,city))