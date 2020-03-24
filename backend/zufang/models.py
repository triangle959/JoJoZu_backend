from django.db import models

from mongoengine import *

# Create your models here.

class Common(Document):
    title = StringField(max_length=100)
    type = StringField(max_length=10)
    lease = StringField(max_length=10)
    image = ListField(max_length=20)
    payment_method = StringField(max_length=10)
    cost = StringField(max_length=10)
    # 押金
    cash_pledge = StringField(max_length=10)
    # 区域
    area = StringField(max_length=10)
    # 是否有中介
    had_agent = IntField()
    service_charge = StringField(max_length=10)
    # 中介费
    agent_cost = StringField(max_length=10)
    # 最近地铁站
    location = StringField(max_length=10)
    # 设施
    support = ListField(max_length=20)
    description = StringField(max_length=500)
    # 更新时间以及更新时间戳
    update_time = StringField(max_length=20)
    update_timestamp = IntField()
    url = StringField(max_length=200)
    # 来源渠道
    source = StringField(max_length=10)
    city = StringField(max_length=10)

class Douban(Document):
    # 标题
    title = StringField(max_length=10)
    # 发布者
    author = StringField(max_length=10)
    # 内容H5
    content = StringField(max_length=5000)
    # 内容正文
    text = StringField(max_length=5000)
    # 租房类型
    lease = StringField(max_length=10)
    # 图片 ArrayList
    image = ListField(max_length=20)
    # 回应数
    replay_num = StringField(max_length=10)
    # 创建时间
    create_time = StringField(max_length=20)
    # 更新时间
    update_time = StringField(max_length=20)
    update_timestamp = IntField()
    # 链接
    url = StringField(max_length=10)
    city = StringField(max_length=10)