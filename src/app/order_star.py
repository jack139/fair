#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/order_star')

# 订单打分
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', order_id='', star='', sign='')

		if '' in (param.app_id, param.session, param.order_id, param.star, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id, param.star])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_user = db.app_user.find_one({'uname':uname},{'coupon':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 订单打分
			db.order_app.update_one({'order_id' : param.order_id, 'user':uname},{
				'$set'  : { 'star': int(param.star) },
				'$push' : { 'history' : (app_helper.time_str(), uname, '订单打分')},
			})
			return json.dumps({'ret' : 0, 'msg' : '订单已打分！'})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
