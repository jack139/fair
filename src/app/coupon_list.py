#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/coupon_list')

# 获取所有优惠券
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

			db_user = db.app_user.find_one({'uname':uname},{'coupon':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 检查是否有新红包
			app_helper.check_hb(uname)

			# 这里应该增加对有效期的检查！！！
			coupon=[]
			unused=0
			for i in db_user['coupon']:
				if app_helper.time_str(format=1)>i[1]: # 过期抵用券不返回 2015-08-22
					continue
				coupon.append({
					'id'     : i[0],
					'valid'  : i[1],
					'cash'   : i[2],
					'status' : 'unused' if i[3]==1 else 'used', 
				})
				unused += (1 if i[3]==1 else 0)

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'coupon'  : coupon,
				'total'   : len(coupon),
				'unused'  : unused,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
