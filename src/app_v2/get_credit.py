#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/get_credit')

# 获取用户余额
class handler:        
	def POST(self, version='v2'):
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

			db_user = db.app_user.find_one({'uname':uname['uname']},{'coupon':1,'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'credit'  : '%.2f' % db_user.get('credit', 0.0)
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
