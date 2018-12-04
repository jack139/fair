#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/coupon_list')

def quick(L):
	if len(L) <= 1: return L
	return quick([a for a in L[1:] if float(a['cash']) > float(L[0]['cash'])]) + L[0:1] + quick([b for b in L[1:] if float(b['cash']) <= float(L[0]['cash'])])

# 获取所有优惠券
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='',session_id='')

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'coupon':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 返回列表排序，可用的按金额排序，过期的沉底
			coupon=[]
			coupon_used=[]
			coupon_expired=[]
			unused=0
			for i in db_user['coupon']:
				if len(i)>4: 
					# (id, 有效期, 金额, 是否已用, 门槛) 2015-09-27
					# 有门槛信息，使用优惠券门槛信息
					msg1 = '满%.1f元使用' % i[4]
				else:
					# 没有门槛信息，使用默认设置
					if float(i[2])==6.0:
						msg1 = '满29.9元使用'
					elif float(i[2])==9.0:
						msg1 = '满39.9元使用'
					else:
						msg1 = '满14.9元使用'

				msg2 = '抵用券'
				msg3 = ''
				if len(i)>5:
					if i[5]=='apple':
						#msg2 = '水果券'
						msg3 = '，须含水果'
					elif i[5]=='b3':
						#msg2 = '整箱券'
						msg3 = '，整箱可用'

				if i[3]==0:
					coupon_used.append({
						'id'     : i[0],
						'valid'  : i[1],
						'cash'   : i[2],
						'status' : 'used', 
						'msg1'   : msg1+msg3,
						'msg2'   : msg2,
					})
				elif app_helper.time_str(format=1)>i[1]: # 过期抵用券不返回 2015-08-22
					coupon_expired.append({
						'id'     : i[0],
						'valid'  : i[1],
						'cash'   : i[2],
						'status' : 'expired', 
						'msg1'   : msg1+msg3,
						'msg2'   : msg2,
					})
				elif i[3]==1:
					coupon.append({
						'id'     : i[0],
						'valid'  : i[1],
						'cash'   : i[2],
						'status' : 'unused', 
						'msg1'   : msg1+msg3,
						'msg2'   : msg2,
					})
					unused += 1
				else: # 未知类型
					coupon_used.append({
						'id'     : i[0],
						'valid'  : i[1],
						'cash'   : i[2],
						'status' : 'used', 
						'msg1'   : msg1+msg3,
						'msg2'   : msg2,
					})

			coupon = quick(coupon)
			coupon.extend(coupon_used)
			coupon.extend(coupon_expired)

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'coupon'  : coupon,
				'total'   : len(coupon),
				'unused'  : unused,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
