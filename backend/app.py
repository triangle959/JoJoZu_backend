#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/9 11:43
# @Author  : zjz
import pymongo
from flask import Flask, jsonify, make_response
from flask_cors import CORS
from flask_restful import reqparse, abort, Api, Resource

app = Flask(__name__)
CORS(app, supports_credentials=True)
api = Api(app)

conn = pymongo.MongoClient("mongodb://zjz:triangle%40123@111.229.148.168:27018/admin?readPreference=primary")
db = conn["JoJoZu"]

@app.after_request
def af_request(resp):
    """
    #请求钩子，在所有的请求发生后执行，加入headers。
    :param resp:
    :return:
    """
    resp = make_response(resp)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET,POST'
    resp.headers['Access-Control-Allow-Headers'] = 'x-requested-with,content-type'
    resp.headers['content'] = 'application/json'
    resp.headers['chartset'] = 'utf-8'
    return resp

TODOS = {
    'todo1': {'task': 'build an API'},
    'todo2': {'task': '?????'},
    'todo3': {'task': 'profit!'},
}


def abort_if_todo_doesnt_exist(todo_id):
    if todo_id not in TODOS:
        abort(404, message="Todo {} doesn't exist".format(todo_id))


parser = reqparse.RequestParser()
parser.add_argument('task')
parser.add_argument('pageIndex', type=int, help="'pageIndex' must be integer!")
parser.add_argument('pageSize', type=int, help="'pageSize' must be integer!")
parser.add_argument('city', type=str, help="'city' is must parameter!")


# Todo
# shows a single todo item and lets you delete a todo item
class Todo(Resource):
    def get(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        return TODOS[todo_id]

    def delete(self, todo_id):
        abort_if_todo_doesnt_exist(todo_id)
        del TODOS[todo_id]
        return '', 204

    def put(self, todo_id):
        args = parser.parse_args()
        task = {'task': args['task']}
        TODOS[todo_id] = task
        return task, 201


class CommonList(Resource):
    def get(self):
        data = parser.parse_args(strict=True)
        pageIndex = data.get('pageIndex')
        pageSize = data.get('pageSize')
        city = data.get('city')
        data_list = []
        for item in db['common'].find({'city': city}).sort([("update_timestamp",-1)]).skip(pageIndex).limit(pageSize):
            item['_id'] = str(item['_id'])
            data_list.append(item)
        return jsonify({'status_code': 200, 'list': data_list, 'pageTotal': db['common'].count_documents({"city":city})})


class DoubanList(Resource):
    def get(self):
        data = parser.parse_args(strict=True)
        pageIndex = data.get('pageIndex')
        pageSize = data.get('pageSize')
        city = data.get('city')
        data_list = []
        for item in db['douban'].find({'city': city}).sort([("update_timestamp",-1)]).skip(pageIndex).limit(pageSize):
            item['_id'] = str(item['_id'])
            data_list.append(item)
        return jsonify({'status_code': 200, 'list': data_list, 'pageTotal': db['douban'].count_documents({"city":city})})


# Actually setup the Api resource routing here
api.add_resource(CommonList, '/common')
api.add_resource(DoubanList, '/douban')
api.add_resource(Todo, '/todos/<todo_id>')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)