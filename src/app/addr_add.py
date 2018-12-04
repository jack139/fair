#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper

db = setting.db_web

url = ('/app/addr_add')

# 新增收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', name='', tel='', addr='', sign='')

		if '' in (param.app_id, param.session, param.name, param.tel, param.addr, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.name, param.tel, param.addr])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			# 需要判断地址是否有对应门店，否则不在送货范围内
			# app_helper.check_address()

			# 更新个人资料
			new_addr = (
					app_helper.my_rand(),
					param.name.strip(),
					param.tel.strip(), 
					param.addr.strip(),
					int(time.time())
			)
			r = db.app_user.update_one({'uname':uname}, {'$push' : {'address' : new_addr}})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr_id'  : new_addr[0],
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
