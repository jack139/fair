#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/customer_voice')

# 新增收货地址
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version
		param = web.input(app_id='', session='', voice='', sign='')

		if '' in (param.app_id, param.session, param.voice, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.voice])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			# 存入db
			db.customer_voice.insert_one({
				'uname' : uname['uname'],
				'voice' : param.voice,
				'time'  : app_helper.time_str(),
			})

			# 返回
			return json.dumps({'ret' : 0})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
