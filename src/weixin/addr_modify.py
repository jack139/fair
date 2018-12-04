#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/addr_modify')

# 修改收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', addr_id='', name='', tel='', addr='')

		if '' in (param.addr_id, param.name, param.tel, param.addr):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			# 需要判断地址是否有对应门店，否则不在送货范围内
			# app_helper.check_address()

			# 查找并修改收货地址
			r = db.app_user.find_one({'openid':uname['openid']}, {'address' : 1})

			new_addr = []
			for i in r['address']:
				if i[0]==param.addr_id:
					new_addr.append((
						param.addr_id,
						param.name.strip(),
						param.tel.strip(), 
						param.addr.strip(),
						int(time.time())
					))
				else:
					new_addr.append(i)

			r = db.app_user.update_one({'openid':uname['openid']}, {'$set' : {'address' : new_addr}})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr_id' : param.addr_id,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
