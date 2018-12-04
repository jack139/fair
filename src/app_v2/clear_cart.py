#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v3)/clear_cart')

# 支付宝下单
class handler:        
	def POST(self, version='v3'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', secret='', sign='')

		if '' in (param.app_id, param.session, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.secret])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			#db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

			# 清除用户购物车信息
			db_cart = db.app_user.update_one({'uname':uname['uname']},{'$set':{'cart_order.%s'%param.session:''}})

			return json.dumps({'ret' : 0})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
