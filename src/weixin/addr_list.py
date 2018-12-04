#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/addr_list')

def quick(L):
     if len(L) <= 1: return L
     return quick([a for a in L[1:] if a['tick'] > L[0]['tick']]) + L[0:1] + quick([b for b in L[1:] if b['tick'] <= L[0]['tick']])

# 获取所有收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='')

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'address':1})
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

			#print addr
			addr2 = quick(addr)
			#print addr2

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr'  : addr2,
				'total' : len(addr2),
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
