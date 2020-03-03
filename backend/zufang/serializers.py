#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/2/27 14:37
# @Author  : zjz
from rest_framework_mongoengine import serializers
from . import models


class commonSerializer(serializers.DocumentSerializer):
    class Meta:
        model = models.Common
        fields = '__all__'


class doubanSerializer(serializers.DocumentSerializer):
    class Meta:
        model = models.Douban
        fields = '__all__'
