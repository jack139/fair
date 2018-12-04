#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/addr_list')

def quick(L):
	if len(L) <= 1: return L
	return quick([a for a in L[1:] if a['tick'] > L[0]['tick']]) + L[0:1] + quick([b for b in L[1:] if b['tick'] <= L[0]['tick']])

# 获取所有收货地址
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

			db_user = db.app_user.find_one({'uname':uname['uname']},{'address':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			addr=[]
			# v1 address [id, 收货人, 收货电话, 地址]
			# v2 address [id, 收货人, 收货电话, 地址, 修改时间戳]
			# v2 address [id, 收货人, 收货电话, 地址, 修改时间戳, gps]
			# v3 address [id, 收货人, 收货电话, 地址, 修改时间戳, gps, 提示标题, 提示地址, 城市]
			for i in db_user['address']:
				ad={
					'id'   : i[0],
					'name' : i[1],
					'tel'  : i[2],
					'addr' : i[3],
					'tick' : i[4] if len(i)>4 else 0,
				}
				if version=='v3':
					if len(i)>6:
						ad['title']=i[6]
						ad['detail']=i[7]
						ad['city']=i[8]
						if len(i)>5 and i[5]['lat']>0:
							ad['loc']='%f,%f' % (i[5]['lat'],i[5]['lng'])
						else:
							ad['loc']=''
					else:
						ad['title']=''
						ad['detail']=''
						ad['city']='上海'
						if len(i)>5 and i[5]['lat']>0:
							ad['loc']='%f,%f' % (i[5]['lat'],i[5]['lng'])
						else:
							ad['loc']=''

				addr.append(ad)

			addr2 = quick(addr)

			print addr2
			
			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr'  : addr2,
				'total' : len(addr2),
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
