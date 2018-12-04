#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/order_pay')

# 支付完成
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', order_id='', pay_type='', data='')
		print param

		if '' in (param.order_id, param.pay_type):
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
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 支付操作：1，记录订单支付，2.改变订单状态，3.修改库存显示 ！！！！！！

			# 获得订单
			db_order = db.order_app.find_one(
				{'order_id' : param.order_id},
				#{'status':1, 'cart':1, 'due':1, 'shop':1}
				{'_id':0}
			)
			if db_order==None:
				return json.dumps({'ret' : -3, 'msg' : '未找到订单！'})

			# 支付宝和微信支付订单，已PAID说明提前收到异步通知
			if db_order['status']=='PAID' and param.pay_type in ('ALIPAY','WXPAY'):
				# 记录此次调用
				db.order_app.update_one(
					{
						'order_id' : param.order_id,
					},
					{
						'$set' : { 
							'pay_type'   : param.pay_type,
							'pay'        : db_order['due'],
							'paid2_time' : app_helper.time_str(),
							'paid2_tick' : int(time.time()),
						},
						'$push' : { 'history' : (app_helper.time_str(), uname['openid'], '提交付款')},
					}
				)
				return json.dumps({'ret' : 0, 'data' : {
					'order_id' : param.order_id,
					'due'      : db_order['due'],
					'paid'     : db_order['due'],
					'status'   : '已支付'
				}})

			# 只能处理未支付订单
			if db_order['status']!='DUE':
				return json.dumps({'ret' : -3, 'msg' : '不是待付款订单！'})

			# 微信支付未到账处理
			if param.pay_type in ('ALIPAY', 'WXPAY'):
				# 更新销货单信息，
				r = db.order_app.find_one_and_update(
					{
						'order_id' : param.order_id,
						'status'   : 'DUE'
					},
					{
						'$set' : { 
							'status'     : 'PREPAID', 
							'pay_type'   : param.pay_type,
							'pay'        : db_order['due'],
							'paid2_time' : app_helper.time_str(),
							'paid2_tick' : int(time.time()),
							'pay_data'   : param.data,
						},
						'$push' : { 'history' : (app_helper.time_str(), uname['openid'], '提交付款')},
					},
					{'status':1}
				)
				# 如果不是DUE，说明已收到异步通知
				if r==None:
					db.order_app.update_one(
						{
							'order_id' : param.order_id,
						},
						{
							'$set' : { 
								'pay_type'   : param.pay_type,
								'pay'        : db_order['due'],
								'paid2_time' : app_helper.time_str(),
								'paid2_tick' : int(time.time()),
							},
							'$push' : { 'history' : (app_helper.time_str(), uname['openid'], '提交付款')},
						}
					)

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'order_id' : param.order_id,
				'due'      : db_order['due'],
				'paid'     : db_order['due'],
				'status'   : '已支付',
				'alert'    : False,
				'message'  : '测试信息，还未收到异步通知',
				'url'      : 'http://app-test.urfresh.cn'
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
