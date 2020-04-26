import time
import datetime
from collections import defaultdict

from django.db.models import Count
from django.http import request, HttpResponse, JsonResponse
from .models import Common, Douban
from django.shortcuts import render
# Create your views here.
from . import models
from . import serializers
from rest_framework_mongoengine import generics
from rest_framework.pagination import CursorPagination, LimitOffsetPagination
from mongoengine import Q


class commonView(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        if request.GET.get('city'):
            print(request.GET.get('city'))
            queryset = Common.objects.filter(city=request.GET.get('city')).filter(
                type__contains=request.GET.get('type')).filter(cost__gte=request.GET.get('min')).filter(
                cost__lte=request.GET.get('max')).order_by('-update_timestamp')
        else:
            queryset = Common.objects.all().order_by('-update_timestamp')
        serializer_class = serializers.commonSerializer
        # 偏移分页，请求参数为?limit=11&offset=5， 移除以下则返回DRF自带页面
        # 创建分页对象
        page = LimitOffsetPagination()
        # 在数据库中获取分页的数据
        page_list = page.paginate_queryset(queryset, request, view=self)
        # 对分页进行序列化
        ser = serializer_class(instance=page_list, many=True)
        data_dict = {}
        data_dict.update({"total_count": Common.objects.count()})
        data_dict.update({"city_count": {}})
        for item in Common.objects.aggregate(
                [{"$group": {"_id": "$city", "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}}]):
            data_dict["city_count"].update({item["_id"]: item["count"]})
        # return page.get_paginated_response(ser.data)
        return JsonResponse({
            'status': 200,
            'msg': 'success',
            'data': ser.data,
            'pageTotal': data_dict["city_count"].get(request.GET.get('city'))
        }, json_dumps_params={'ensure_ascii': False})


class doubanView(generics.ListCreateAPIView):
    def get(self, request, *args, **kwargs):
        if request.GET.get('city') and request.GET.get('lease'):
            queryset = Douban.objects.filter(city=request.GET.get('city')).filter(
                lease=request.GET.get('lease')).order_by('-update_timestamp')
        elif request.GET.get('lease'):
            queryset = Douban.objects.filter(lease=request.GET.get('lease')).order_by('-update_timestamp')
        elif request.GET.get('city'):
            queryset = Douban.objects.filter(city=request.GET.get('city')).order_by('-update_timestamp')
        else:
            queryset = Douban.objects.all().order_by('-update_timestamp')
        # page_total = len(queryset)    #这里如果取len(queryset) 会进行多次遍历
        serializer_class = serializers.doubanSerializer
        # 偏移分页，请求参数为?limit=11&offset=5， 移除以下则返回DRF自带页面
        # 创建分页对象
        page = LimitOffsetPagination()
        # 在数据库中获取分页的数据
        page_list = page.paginate_queryset(queryset, request, view=self)
        # 对分页进行序列化
        ser = serializer_class(instance=page_list, many=True)
        data_dict = {}
        data_dict.update({"total_count": Douban.objects.count()})
        data_dict.update({"city_count": {}})
        page_total = 0
        for item in Douban.objects.aggregate(
                [{"$group": {"_id": {
                    "city": "$city",
                    "lease": "$lease"
                }, "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}}]):
            if request.GET.get('lease') and item['_id']["lease"] == request.GET.get('lease'):
                page_total += item["count"]
            if request.GET.get('city') and item['_id']["city"] == request.GET.get('city'):
                page_total += item["count"]
            if not request.GET.get('lease') and not request.GET.get('city'):
                page_total += item["count"]
        # return page.get_paginated_response(ser.data)
        return JsonResponse({
            'status': 200,
            'msg': 'success',
            'data': ser.data,
            'pageTotal': page_total
        }, json_dumps_params={'ensure_ascii': False})


# 1. 接口 返回有多少条数据 done
# 2. 筛选总和，筛选重复的城市个数 done
# 3. 修改查询页，排序功能，对插入时间和更新时间进行排序
def getCommonCount(request):
    data_dict = {}
    data_dict.update({"total_count": Common.objects.count()})
    data_dict.update({"city_count": {}})
    for item in Common.objects.aggregate(
            [{"$group": {"_id": "$city", "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}}]):
        data_dict["city_count"].update({item["_id"]: item["count"]})

    return JsonResponse({
        'status': 200,
        'msg': 'success',
        'data': data_dict
    }, json_dumps_params={'ensure_ascii': False})


def controlView(request):
    today = datetime.date.today()
    startday = today - datetime.timedelta(days=8)
    start_time = int(time.mktime(time.strptime(str(startday), '%Y-%m-%d')))
    end_time = int(time.mktime(time.strptime(str(today), '%Y-%m-%d'))) - 1
    print(end_time)
    # 统计不同城市7日内的租金变化
    result1 = list(Common.objects.aggregate([
        {"$match": {
            "$and": [
                {"update_timestamp": {"$gt": start_time}},
                {"update_timestamp": {"$lt": end_time}}
            ]
        }},
        {"$project": {
            "day": {"$substrCP": ["$update_time", 5, 5]},
            "city": "$city",
            "cost": "$cost"
        }},
        {"$group": {
            "_id": {
                "day": "$day",
                "city": "$city"
            },
            "count": {"$sum": 1},
            "avg": {"$avg": "$cost"},
            "min": {"$min": "$cost"},
            "max": {"$max": "$cost"}
        }}
    ]))
    deal_result1 = []
    city_list = []
    date_set = set()
    for item in sorted(result1, key=lambda r: r["_id"]["day"]):
        if item["_id"].get("city"):
            if item["_id"]["city"] not in city_list:
                city_list.append(item["_id"]["city"])
                date_set.add(item["_id"]["day"])
                deal_result1.append({
                    "name": item["_id"]["city"],
                    "avg_data": [int(item["avg"])],
                    "count_data": [int(item["count"])],
                    "max_data": [int(item["max"])],
                    "min_data": [int(item["min"])],
                })
            else:
                deal_result1[city_list.index(item["_id"]["city"])]["avg_data"].append(int(item["avg"]))
                deal_result1[city_list.index(item["_id"]["city"])]["count_data"].append(int(item["count"]))
                deal_result1[city_list.index(item["_id"]["city"])]["max_data"].append(int(item["max"]))
                deal_result1[city_list.index(item["_id"]["city"])]["min_data"].append(int(item["min"]))
                date_set.add(item["_id"]["day"])
    date_set = list(sorted(date_set))
    # 拼接各个渠道数量统计
    result2 = list(Common.objects.aggregate([
        {"$match": {
            "update_timestamp": {"$gt": end_time}
        }},
        {"$group": {
            "_id": "$source",
            "count": {"$sum": 1},
        }}

    ]))
    result3 = list(
        Common.objects.aggregate([{"$group": {"_id": "$source", "dups": {"$addToSet": "$_id"}, "count": {"$sum": 1}}}]))
    deal_result2 = {}
    for index, j in enumerate(result2):
        if not deal_result2.get("today_num"):
            deal_result2.update({"today_num": [{"source": j["_id"], "sum": j["count"]}]})
        else:
            deal_result2["today_num"].append({"source": j["_id"], "sum": j["count"]})
    for index, k in enumerate(result3):
        if not deal_result2.get("all_num"):
            deal_result2.update({"all_num": [{"source": k["_id"], "sum": k["count"]}]})
        else:
            deal_result2["all_num"].append({"source": k["_id"], "sum": k["count"]})
    result4 = list(Douban.objects.aggregate(
        [{"$match": {"update_timestamp": {"$gt": end_time}}}, {"$group": {"_id": "Total", "count": {"$sum": 1}}}]))
    deal_result2["today_num"].append({"source": "豆瓣小组", "sum": result4[0]["count"] if result4 else 0})
    deal_result2["all_num"].append({"source": "豆瓣小组", "sum": Douban.objects.count()})
    return JsonResponse({
        'status': 200,
        'msg': 'success',
        'data': {
            "left": {
                "xAxis": date_set,
                "chart_data": deal_result1
            },
            "right": {
                "data": deal_result2
            }
        }
    }, json_dumps_params={'ensure_ascii': False})


class searchForView(generics.ListCreateAPIView):
    """
    平台搜索接口，搜索词可以是title，或者是内容
    :param request:
    :return:
    """
    def post(self, request, *args, **kwargs):
        collection = request.POST.get('object')
        keyword = request.POST.get('keyword')
        status_code = 200
        message = "ok"

        if collection == "common":
            data = Common.objects(Q(description__contains=keyword) | Q(title__contains=keyword)).order_by(
                '-update_timestamp')
            serializer_class = serializers.commonSerializer
        elif collection == "douban":
            data = Douban.objects(Q(text__contains=keyword) | Q(title__contains=keyword)).order_by('-update_timestamp')
            serializer_class = serializers.doubanSerializer
        else:
            status_code = 400
            message = 'no this collection!'

        if data:
            page = LimitOffsetPagination()
            # 在数据库中获取分页的数据
            page_list = page.paginate_queryset(data, request, view=self)
            # 对分页进行序列化
            ser = serializer_class(instance=page_list, many=True)
            return JsonResponse(
                {"status_code": status_code,
                 "message": message,
                 "data": ser.data,
                 "pageTotal": len(data)
                 })
        else:
            return JsonResponse(
                {"status_code": status_code, "message": message, "data": ""})
