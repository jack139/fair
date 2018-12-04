#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web  # mongo_db 连接

url = ('/bi/report') # 访问的 url 路径

# BI数据返回json
class handler:
	def GET(self):  # GET 处理
		web.header("Content-Type", "application/json")
		result={'a':'6'}
		if helper.logged(helper.PRIV_USER,'BI_REPORT'): # 权限检查
			param = web.input(id='') # 输入的参数

			# 数据查询
			# 返回放在 result里
			result = { 'data' : 'test'}
		print result
		return json.dumps(result)

	def POST(self):  # POST 处理
		web.header("Content-Type", "application/json")
		result={}
		if helper.logged(helper.PRIV_USER,'BI_REPORT'): # 权限检查
			param = web.input(id='') # 输入的参数

			# 数据查询
			# 返回放在 result里
			result = { 'data' : 'test'}
		#print result
		return json.dumps(result)

