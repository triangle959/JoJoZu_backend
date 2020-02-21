#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/4 11:33
# @Author  : zjz
import json
import time

import requests


def time_standard(press_time):
    try:
        new_time = press_time.replace('-', ' ').replace('/', ' ').replace('.', ' ').replace(':', ' ').replace(
            '年', ' ').replace('月', ' ').replace('日', ' ')
        time_list = [i for i in new_time.split(" ") if i]
        if len(time_list[1]) == 1:
            time_list[1] = '0' + time_list[1]
        if len(time_list[2]) == 1:
            time_list[2] = '0' + time_list[2]
        if len(time_list) > 3:
            if len(time_list[3]) == 1:
                time_list[3] = '0' + time_list[3]
            if len(time_list[4]) == 1:
                time_list[4] = '0' + time_list[4]
        new_time = "".join(time_list)
        while len(new_time) < 14:
            new_time += '0'
        new_time = '{}-{}-{} {}:{}:{}'.format(new_time[0:4], new_time[4:6], new_time[6:8], new_time[8:10],
                                              new_time[10:12], new_time[12:14])

        timeArray = time.strptime(new_time, "%Y-%m-%d %H:%M:%S")
        return new_time, int(time.mktime(timeArray))
    # except OverflowError:
    #     raise (press_time + "时间处理错误")
    # except ValueError:
    #     raise (press_time + "时间处理错误")
    except Exception:
        print(press_time + "时间处理错误")
        return None, 9999999999


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
    # keyword = "万科蛇口公馆"
    # city = "深圳"
    # a = AreaPosition()
    # location = a.get_geocoder(keyword,city)
    # print(a.get_area(location, city))
    # print(a.get_place(location,city))
    print(time_standard("2019年12月30日"))
    print(time_standard("2020-02-19"))
