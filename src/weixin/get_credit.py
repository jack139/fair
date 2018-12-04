#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/get_credit')

# 获取用户余额
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='',session_id='')

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'coupon':1,'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'credit'  : '%.2f' % db_user.get('credit', 0.0)
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
