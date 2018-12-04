#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/addr_list')

def quick(L):
     if len(L) <= 1: return L
     return quick([a for a in L[1:] if a['tick'] > L[0]['tick']]) + L[0:1] + quick([b for b in L[1:] if b['tick'] <= L[0]['tick']])

# 获取所有收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', secret='', sign='')

		if '' in (param.app_id, param.session, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.secret])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_user = db.app_user.find_one({'uname':uname},{'address':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			addr=[]
			for i in db_user['address']:
				addr.append({
					'id'   : i[0],
					'name' : i[1],
					'tel'  : i[2],
					'addr' : i[3],
					'tick' : i[4] if len(i)>4 else 0,
				})

			addr2 = quick(addr)

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr'  : addr2,
				'total' : len(addr2),
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
