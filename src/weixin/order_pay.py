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

			# 余额支付和支付宝／微信支付未到账处理

			if param.pay_type=='CREDIT':
				# 检查余额是否够支付
				if float(db_order['due'])>db_user.get('credit',0.0):
					return json.dumps({'ret' : -6, 'msg' : '余额不足！'})

				# 使用的优惠券失效
				#db_user = db.app_user.find_one({'uname':r['uname']})

				coupon = []
				if db_order['coupon']!=None:
					for i in db_user['coupon']:
						if i[0]==db_order['coupon'][0]: # 这次使用
							#coupon.append((i[0],i[1],i[2],0))
							i2=list(i)
							i2[3]=0
							coupon.append(i2)
						else:
							coupon.append(i)
				else:
					coupon = db_user['coupon']

				# 更新优惠券
				db.app_user.update_one({'openid':db_order['uname']}, {'$set':{'coupon':coupon}})

				# 正常减库存！
				# item = [ product_id, num, num2, price]
				# k - num 库存数量
				print "修改库存."

				b2 = [] # C端商品
				b3 = [] # B3整箱预售商品
				b3_total = 0.0
				for item in db_order['cart']:
					#r3 = db.sku_store.find_one({'product_id' : item['product_id']},
					#	{'list_in_app':1})
					#if r3['list_in_app']==3: # B3商品不需要改库存
					#	b3_total += float(item['price'])
					#	b3.append(item)
					#	item['title'] = item['title']+u'（整箱预售，次日送达）'
					#	b2.append(item)
					#	continue

					# 买一送一
					if item['product_id'] in app_helper.buy_1_give_1:
						lc_num2 = float(item['num2'])
						item['num2'] = int(lc_num2 + lc_num2)
						item['title'] = item['title'].replace(u'买一送一',u'特惠活动')

					# 过滤数量价格为零的
					if item['num2']==0 and float(item['price'])==0.0:
						continue

					r = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
						{
							'product_id' : item['product_id'],
							'shop'       : db_order['shop'],
						},
						{ 
							'$inc'  : { 
								'num'         : 0-float(item['num2']), # num2 实际购买数量
							 	'pre_pay_num' : float(item['num2']), # 记录预付数量
							}
							#'$push' : { 'history' : (helper.time_str(), 
							#	helper.get_session_uname(), '售出 %s' % str(item['num']))},
						},
						{'_id':1}
					)
					#print r
					if r==None: # 不应该发生
						return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
					else:
						b2.append(item)

					# 更新第3方库存 2015-10-10
					app_helper.elm_modify_num(db_order['shop'], item['product_id'])

				# 检查是否有b3商品, 3种情况
				# 1. b2, b3 都有，拆单
				# 2. 只有b3，站点改为B3站点，保留收货站点
				# 3. 只有b2，保持订单不变
				#print b2
				#print b3
				if len(b3)>0 and (len(b2)-len(b3))>0: # 情况1
					print "拆单"
					r4 = db_order.copy()
					r4['order_id']     = r4['order_id']+u'-b3'
					r4['shop_0']       = r['shop']
					r4['shop']         = ObjectId(setting.B3_shop)
					r4['cart']         = b3
					r4['status']       = 'PAID'
					r4['ali_trade_no'] = param.get('trade_no')
					r4['paid_time']    = param.get('gmt_payment')
					r4['paid_tick']    = int(time.time())
					r4['history']      = [(app_helper.time_str(), 'credit', '余额付款－拆单')]
					r4['total']        = '%.2f' % b3_total
					r4['cost']         = '0.00'
					r4['coupon_disc']  = '0.00'
					r4['first_disc']   = '0.00'
					r4['delivery_fee'] = '0.00'
					r4['due']          = '0.00'
					db.order_app.insert_one(r4) # 增加子订单
				elif len(b3)>0: # 情况 2
					print "订单改到B3站点"
					db.order_app.update_one({'order_id':param.order_id},{'$set' : {
						'shop_0' : r['shop'],
						'shop'   : ObjectId(setting.B3_shop),
					}})
				else: # 情况3，什么都不做
					print "订单保持不变"

				# 更新销货单信息
				db.order_app.update_one({'order_id' : param.order_id,},{
					'$set' : { 
						'status'     : 'PAID', 
						'cart'       : b2,     # 更新购物车  2015-09-11
						'pay_type'   : param.pay_type,
						'pay'        : db_order['due'],
						'paid_time'  : app_helper.time_str(),
						'paid_tick'  : int(time.time()),
					},
					'$push' : { 'history' : (app_helper.time_str(), uname['openid'], '余额付款')},
				})
				# 消费余额
				db.app_user.update_one({'openid' : uname['openid'],},{
					'$inc' : { 
						'credit'     : 0-float(db_order['due']), 
					},
					'$push' : { 
						'history' : (app_helper.time_str(), uname['openid'], 
							'消费余额 %s' % db_order['due'].encode('utf-8'))
					},
				})
			elif param.pay_type in ('ALIPAY', 'WXPAY'):
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
				'status'   : '已支付'
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
