#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/addr_remove')

# 删除收货地址
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', addr_id='', sign='')

		if '' in (param.app_id, param.session, param.addr_id, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.addr_id])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			# 查找并删除收货地址
			r = db.app_user.find_one({'uname':uname['uname']}, {'address' : 1})

			new_addr = []
			for i in r['address']:
				if i[0]==param.addr_id:
					continue
				else:
					new_addr.append(i)

			r = db.app_user.update_one({'uname':uname['uname']}, {'$set' : {'address' : new_addr}})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr_id' : param.addr_id,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
