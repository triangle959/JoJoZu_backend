#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/11/28 11:43
# @Author  : zjz


import os
import sys

sys.path.append("../")  # 解决潜在的路径依赖问题
sys.path.append("../../")  # 解决潜在的路径依赖问题
sys.path.append("../../../")  # 解决潜在的路径依赖问题
sys.path.append("../../../../")  # 解决潜在的路径依赖问题
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print(os.path.dirname(os.path.abspath(__file__)))
from scrapy.cmdline import execute
# 添加当前项目的绝对地址

# 执行 scrapy 内置的函数方法execute，  使用 crawl 爬取并调试

execute(['scrapy', 'crawl', 'beike'])