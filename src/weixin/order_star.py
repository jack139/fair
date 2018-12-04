#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/order_star')

# 订单打分
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', order_id='', star='')

		if '' in (param.order_id, param.star):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'coupon':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 订单打分
			db.order_app.update_one({'order_id' : param.order_id, 'user':{'$in':uname.values()}},{
				'$set'  : { 'star': int(param.star) },
				'$push' : { 'history' : (app_helper.time_str(), uname['openid'], '订单打分')},
			})
			return json.dumps({'ret' : 0, 'msg' : '订单已打分！'})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
