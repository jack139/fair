#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/order_cancel')

# 订单详情
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', order_id='', sign='')

		if '' in (param.app_id, param.session, param.order_id, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_user = db.app_user.find_one({'uname':uname},{'coupon':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 获得订单
			db_order = db.order_app.find_one(
				{'order_id' : param.order_id, 'user':uname},
				{'status':1, 'cart':1, 'due':1, 'shop':1}
			)
			if db_order==None:
				return json.dumps({'ret' : -3, 'msg' : '未找到订单！'})
			elif db_order['status']!='DUE':
				return json.dumps({'ret' : -3, 'msg' : '不是待付款订单！'})

			# 取消订单
			db.order_app.update_one({'order_id' : param.order_id,},{
				'$set'  : { 'status':'CANCEL' },
				'$push' : { 'history' : (app_helper.time_str(), uname, '取消账单')},
			})
			return json.dumps({'ret' : 0, 'msg' : '订单已取消！'})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
