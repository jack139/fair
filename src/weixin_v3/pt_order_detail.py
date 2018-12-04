#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, helper

db = setting.db_web

url = ('/wx/pt_order_detail')

# 我的拼团活动详情页
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', region_id='', pt_order_id='')

		print param

		if '' in (param.pt_order_id, param.region_id):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'coupon':1, 'credit':1})
			if db_user==None: # 不应该发生
				print '-5'
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 刷新订单状态，过期的OPEN活动变为FAIL1, 个人订单已付款的变为FAIL_TO_REFUND
			r2 = db.pt_order.find({
				'status'      : 'OPEN',
				'expire_tick' : {'$lt' : int(time.time()) }
			}, { 'pt_order_id':1 })
			for x in r2:
				# 已付款的已付款的变为FAIL_TO_REFUND
				db.order_app.update_many({'pt_order_id':x['pt_order_id'],'status':'PAID_AND_WAIT'},
					{
						'$set'  : {'status'  : 'FAIL_TO_REFUND', 'man' : 1},
						'$push' : {'history' : (app_helper.time_str(), 'system', '超时成团失败')}
					}
				)
				#过期的OPEN活动变为FAIL1,
				r3 = db.pt_order.find_one_and_update({'_id':x['_id']},
					{
						'$set'  : {'status'  : 'FAIL1'},
						'$push' : {'history' : (app_helper.time_str(), 'system', '超时成团失败')}
					},
					{'member':1}
				)
				print '发微信通知'
				for x in r3['member']:
					print app_helper.wx_reply_msg(x['openid'], '很抱歉，你参加的拼团活动已过24小时，人数不足未能成团，我们将在1-3个工作日内为您安排退款到支付帐户')

			image_host = 'http://%s/image/product' % setting.image_host

			# 获得订单
			#print param.order_id, uname
			db_order = db.pt_order.find_one({
				'pt_order_id'   : param.pt_order_id,
				#'member.openid' : uname['openid'],
			})
			if db_order==None:
				print '-3'
				return json.dumps({'ret' : -3, 'msg' : '未找到订单！'})

			if db_order['status'] in ['WAIT','FAIL3'] or db_order['type']=='SINGLE':
				# 不显示未开团成功订单和单人购买
				print '-4' 
				return json.dumps({'ret' : -4, 'msg' : '忽略的订单！'})

			db_sku = db.pt_store.find_one({'tuan_id':db_order['tuan_id']})
			image = ['%s/%s/%s' % (image_host, x[:2], x) for x in db_sku['image']]

			# 当前用户身份
			position = 'VISITOR'
			member = []
			for i in db_order['member']:
				if i['openid']==uname['openid']:
					position = i['position']

				r2 = db.app_user.find_one({'openid':i['openid']},{'wx_nickname':1,'wx_headimgurl':1})
				member.append({
					'name'     : r2.get('wx_nickname','???'), # 微信中文昵称
					'position' : i['position'],
					'time'     : i['time'],
					'image'    : r2.get('wx_headimgurl',''), # 取自微信头像
				})

			# 准备返回数据
			now_tick = int(time.time())
			data = {
				"region_id"   : db_order['region_id'], 
				"tuan_id"     : db_order['tuan_id'],
				'pt_order_id' : db_order['pt_order_id'],
				'position'    : position,
				"title1"      : db_sku['title'],
				"image"       : image,
				"status"      : db_order['status'],
				"due"         : db_sku['tuan_price'],
				"type"        : '%d人团'%db_sku['tuan_size'],
				"need"        : db_order['need'],              
				"time_remain" : max(db_order['expire_tick'] - now_tick, 0),
				"time_used"   : (now_tick - db_order['create_tick']) if not db_order.has_key('succ_tick') else (db_order['succ_tick'] - db_order['create_tick']),
				"members"     : member,
			}

			#print data

			return json.dumps({'ret' : 0, 'data' : data})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
