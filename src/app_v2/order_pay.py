#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper #, jpush

db = setting.db_web

url = ('/app/(v2|v3)/order_pay')

# 支付完成
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', order_id='', pay_type='', data='', sign='')
		print param

		if '' in (param.app_id, param.session, param.order_id, param.pay_type, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, 
					param.order_id, param.pay_type, param.data])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_user = db.app_user.find_one({'uname':uname['uname']},{'coupon':1, 'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 支付操作：1，记录订单支付，2.改变订单状态，3.修改库存显示 ！！！！！！

			# 获得订单
			db_order = db.order_app.find_one(
				{'order_id' : param.order_id},
				#{'status':1, 'cart':1, 'due':1, 'shop':1}
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
							'pay'        : db_order.get('due3', db_order['due']),
							'paid2_time' : app_helper.time_str(),
							'paid2_tick' : int(time.time()),
						},
						'$push' : { 'history' : (app_helper.time_str(), uname['uname'], '提交付款')},
					}
				)
				return json.dumps({'ret' : 0, 'data' : {
					'order_id' : param.order_id,
					'due'      : db_order.get('due3', db_order['due']),
					'paid'     : db_order.get('due3', db_order['due']),
					'status'   : '已支付',
					'alert'    : False,
					'message'  : '测试信息, 已经收到异步通知了',
					'url'      : 'http://app-test.urfresh.cn'
				}})

			# 只能处理未支付订单
			if db_order['status']!='DUE':
				return json.dumps({'ret' : -3, 'msg' : '不是待付款订单！'})

			# 余额支付和支付宝／微信支付未到账处理

			if param.pay_type=='CREDIT':
				# 余额支付0元提交的问题，原因未知 2015.08.20
				if round(float(db_order['due']),2)<=0.0:
					return json.dumps({'ret' : -2, 'msg' : '参数错误'})

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

				# 未处理首单送券的逻辑

				# 更新优惠券
				db.app_user.update_one({'uname':db_order['uname']}, {'$set':{'coupon':coupon}})

				# 邀请码用户送抵用券 2015-10-24
				invitation = db_user.get('invitation', '')
				if invitation!='' and db_user.get('invite_coupon_has_sent', 0)==0: # 已填邀请码并且未送过券
					coupon_user = db.app_user.find_one({'my_invit_code':invitation},{'uname':1})
					if coupon_user:
						# 送邀请码用户抵用券
						print '送邀请码用户抵用券'
						valid = app_helper.time_str(time.time()+3600*24*30, 1)
						db.app_user.update_one({'uname':coupon_user['uname']},{'$push':{
							'coupon' : (app_helper.my_rand(), valid, '5.00', 1, 19.9, 'apple')
						}})
						# 设置已送标志
						db.app_user.update_one({'uname':r['uname']}, {'$set':{'invite_coupon_has_sent':1}})

				# 正常减库存！
				# item = [ product_id, num, num2, price]
				# k - num 库存数量
				print "修改库存."

				b2 = [] # C端商品
				b3 = [] # B3整箱预售商品
				b3_total = 0.0
				for item in db_order['cart']:
					# 记录销售量
					db.sku_store.update_one({'product_id' : item['product_id']},
						{'$inc' : {'volume' : float(item['num2'])}}
					)

					#r3 = db.sku_store.find_one({'product_id' : item['product_id']},
					#	{'list_in_app':1})
					#if r3['list_in_app']==3: # B3商品不需要改库存
					#	b3_total += float(item['price'])
					#	b3.append(item)
					#	item['title'] = item['title']+u'（整箱预售，次日送达）'
					#	b2.append(item)
					#	continue

					# 买一送一
					if item.has_key('numyy'): # v3 2015-10-25
						if item['product_id'] in app_helper.buy_X_give_Y.keys():
							print '买X送Y'
							#item['num2'] = int(float(item['num2']) + float(item['numyy']))
							#item['title'] = item['title'] + u'特惠活动'
					else:
						if item['product_id'] in app_helper.buy_1_give_1:
							print '买一送一'
							lc_num2 = float(item['num2'])
							item['num2'] = int(lc_num2 + lc_num2)
							item['title'] = item['title'].replace(u'买一送一',u'特惠活动')

					# 过滤数量价格为零的
					if item['num2']==0 and float(item['price'])==0.0:
						continue

					# num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
					num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
					r = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
						{
							'product_id' : item['product_id'],
							'shop'       : db_order['shop'],
						},
						{ 
							'$inc'  : { 
								'num'         : 0-num_to_change, # num2 实际购买数量
							 	'pre_pay_num' : num_to_change, # 记录预付数量
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
					r4['shop_0']       = db_order['shop']
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
					# 如果订单地址不再配送范围，则由b3直接发出， 2015-10-18
					if db_order.get('poly_shop', 1)==1: # 默认到店配送
						print 'b3配送到店'
						shop_0 = db_order['shop']
					else:
						print 'b3直接发货'
						shop_0 = ObjectId(setting.B3_shop)
					db.order_app.update_one({'order_id':param.order_id},{'$set' : {
						'shop_0' : shop_0,
						'shop'   : ObjectId(setting.B3_shop),
					}})
				else: # 情况3，什么都不做
					print "订单保持不变"

				# 推送通知
				#if len(db_order['uname'])==11 and db_order['uname'][0]=='1':
				#	jpush.jpush('已收到您的付款，我们会尽快处理。', db_order['uname'])

				# 更新销货单信息
				db.order_app.update_one({'order_id' : param.order_id},{
					'$set' : { 
						'status'     : 'PAID', 
						'cart'       : b2,     # 更新购物车  2015-09-11
						'pay_type'   : param.pay_type,
						'pay'        : db_order['due'],
						'paid_time'  : app_helper.time_str(),
						'paid_tick'  : int(time.time()),
						'credit_total' : db_order['due'], # 2015-11-24
					},
					'$push' : { 'history' : (app_helper.time_str(), uname['uname'], '余额付款')},
				})
				# 消费余额
				db.app_user.update_one({'uname' : uname['uname'],},{
					'$inc' : { 
						'credit'     : 0-float(db_order['due']), 
					},
					'$push' : { 
						'credit_history' : (  # 专门记录余额消费
							app_helper.time_str(), 
							'消费余额',
							'-%.2f' % float(db_order['due'].encode('utf-8')),
							'订单: %s' % param.order_id.encode('utf-8')
						)
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
							'pay'        : db_order.get('due3', db_order['due']),
							'paid2_time' : app_helper.time_str(),
							'paid2_tick' : int(time.time()),
							'pay_data'   : param.data,
						},
						'$push' : { 'history' : (app_helper.time_str(), uname['uname'], '提交付款')},
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
								'pay'        : db_order.get('due3', db_order['due']),
								'paid2_time' : app_helper.time_str(),
								'paid2_tick' : int(time.time()),
							},
							'$push' : { 'history' : (app_helper.time_str(), uname['uname'], '提交付款')},
						}
					)

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'order_id' : param.order_id,
				'due'      : db_order.get('due3', db_order['due']),
				'paid'     : db_order.get('due3', db_order['due']),
				'status'   : '已支付',
				'alert'    : False,
				'message'  : '测试信息，还未收到异步通知',
				'url'      : 'http://app-test.urfresh.cn'
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
