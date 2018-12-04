#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/coupon_list')

def quick(L):
	if len(L) <= 1: return L
	return quick([a for a in L[1:] if float(a['cash']) > float(L[0]['cash'])]) + L[0:1] + quick([b for b in L[1:] if float(b['cash']) <= float(L[0]['cash'])])

# 获取所有优惠券
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

			db_user = db.app_user.find_one({'uname':uname['uname']},
				{'coupon':1,'my_invit_code':1,'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 检查是否有新红包
			app_helper.check_hb(uname['uname'])

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

			if db_user.has_key('my_invit_code') and len(db_user['my_invit_code'])>0:
				my_invit_code = db_user['my_invit_code']
			else: # 设置我的邀请码
				my_invit_code = app_helper.my_rand(8,1)
				db.app_user.update_one({'uname':uname['uname']},
					{'$set':{'my_invit_code':my_invit_code}}
				)
			# 返回
			#print coupon
			if version=='v2':
				return json.dumps({'ret' : 0, 'data' : {
					'coupon'     : coupon,
					'total'      : len(coupon),
					'unused'     : unused,
					'invitation' : my_invit_code, 
					'service_tel': '400-966-9966', # 客服电话
				}})
			elif version=='v3':
				return json.dumps({'ret' : 0, 'data' : {
					'coupon'     : coupon,
					'total'      : len(coupon),
					'unused'     : unused,
					'invitation' : my_invit_code, 
					'url'        : 'http://wx.urfresh.cn/static/appweb/Inv_friends.html',
					'url2'       : 'http://wx.urfresh.cn/static/appweb/Inv_friends_wx.html?%s' % uname['uname'],
					'detail'     : '每邀请一个好友使用此邀请码注册U掌柜并下单，可获满20元减5元抵用券一张。', # 邀请码详情
					'title'      : '您的朋友发了22元水果大礼包，快来一起尝鲜吧！', # 分享标题
					'title2'     : '凭邀请码注册领取，APP下单，下单后1小时送达，不满意退款！', # 分享内容
					'service_tel': '400-966-9966', # 客服电话
					'credit'     : '%.2f' % db_user.get('credit', 0),
				}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
