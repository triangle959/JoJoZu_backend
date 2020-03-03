#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/2/27 14:40
# @Author  : zjz


from django.urls import path
from .views import commonView, getCommonCount
from .views import doubanView
urlpatterns = [
    path('common', commonView.as_view(), name='common'),
    path('douban', doubanView.as_view(), name='douban'),
    path('common/count', getCommonCount, name='common_count')
]