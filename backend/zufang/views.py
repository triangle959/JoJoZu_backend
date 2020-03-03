from django.db.models import Count
from django.http import request, HttpResponse, JsonResponse
from .models import Common, Douban
from django.shortcuts import render

# Create your views here.
from . import models
from . import serializers
from rest_framework_mongoengine import generics
from rest_framework.pagination import CursorPagination, LimitOffsetPagination


class commonView(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        if request.GET.get('city'):
            print(request.GET.get('city'))
            queryset = Common.objects.filter(source=request.GET.get('city')).order_by('update_timestamp')
        else:
            queryset = Common.objects.all().order_by('update_timestamp')
        serializer_class = serializers.commonSerializer
        # 偏移分页，请求参数为?limit=11&offset=5， 移除以下则返回DRF自带页面
        # 创建分页对象
        page = LimitOffsetPagination()
        # 在数据库中获取分页的数据
        page_list = page.paginate_queryset(queryset, request, view=self)
        # 对分页进行序列化
        ser = serializer_class(instance=page_list, many=True)
        # return page.get_paginated_response(ser.data)
        return JsonResponse({
            'status': 200,
            'msg': 'success',
            'data': ser.data
        }, json_dumps_params={'ensure_ascii': False})


class doubanView(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        queryset = Douban.objects.all().order_by('update_timestamp')
        serializer_class = serializers.commonSerializer
        # 偏移分页，请求参数为?limit=11&offset=5， 移除以下则返回DRF自带页面
        # 创建分页对象
        page = LimitOffsetPagination()
        # 在数据库中获取分页的数据
        page_list = page.paginate_queryset(queryset, request, view=self)
        # 对分页进行序列化
        ser = serializer_class(instance=page_list, many=True)
        # return page.get_paginated_response(ser.data)
        return JsonResponse({
            'status': 200,
            'msg': 'success',
            'data': ser.data
        }, json_dumps_params={'ensure_ascii': False})


# 1. 接口 返回有多少条数据 done
# 2. 筛选总和，筛选重复的城市个数 done
# 3. 修改查询页，排序功能，对插入时间和更新时间进行排序
def getCommonCount(request):
    data_dict = {}
    data_dict.update({"total_count": Common.objects.count()})
    data_dict.update({"city_count": {}})
    for item in Common.objects.aggregate([{"$group": {"_id": "$city", "dups": {"$addToSet": "$_id" }, "count":{"$sum": 1 }}}]):
        data_dict["city_count"].update({item["_id"]: item["count"]})

    return JsonResponse({
        'status': 200,
        'msg': 'success',
        'data': data_dict
    }, json_dumps_params={'ensure_ascii': False})