#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper
from order_checkout import checkout

db = setting.db_web

url = ('/app/(v3)/creditpay')

# 余额下单
class handler:        
	def POST(self, version='v3'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', order_id='', total='', note='', sign='')

		print param

		if '' in (param.app_id, param.session, param.total, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id, param.total, param.note])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			#db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

			db_user = db.app_user.find_one({'uname':uname['uname']},{'credit':1})

			if len(param.order_id)>0:
				print param.order_id

				db_order = db.order_app.find_one({'order_id':param.order_id})
				if db_order['status']!='DUE':
					print '============================== -100'
					return json.dumps({'ret' : -100, 'msg' : '订单状态变化，请确认'})

				ret_json = checkout(version, uname, {
					'session'   : param.session,
					'order_id'  : param.order_id,
					'shop_id'   : str(db_order['shop']),
					'addr_id'   : db_order['address'][0],
					'coupon_id' : db_order['coupon'][0] if float(db_order['coupon_disc'])>0 else '',
					'cart'      : json.dumps(db_order['cart']),
					'app_id'    : param.app_id,
					'use_credit': '1' if float(db_order.get('use_credit','0'))>0 else '', #2015-11-19
				})
				if ret_json['ret']<0:
					# checkout 出错
					return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

				if float(ret_json['data']['use_credit'])!=float(db_order['use_credit']): # 不用判断due3，因为全额用余额支付
					# checkout后金额有变化，说明库存或优惠券有变化
					print 'checkout后金额有变化，说明库存或优惠券有变化'
					db.order_app.update_one({'order_id':param.order_id},{
						'$set'  : {'status': 'CANCEL'},
						'$push' : {'history':(app_helper.time_str(), uname['uname'], '订单取消(余额)')}
					})
					print '============================== -100'
					return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，订单已取消，请重新下单'})

				# 判断余额
				if float(db_order['due'])>db_user.get('credit', 0.0):
					print '============================== -100'
					return json.dumps({'ret' : -100, 'msg' : '余额不足'})

				# 可支付
				db.order_app.update_one({'order_id':param.order_id},{
					'$push' : {'history':(app_helper.time_str(), uname['uname'], '提交余额支付2')}
				})
				return json.dumps({'ret' : 0, 'order_id' : param.order_id})

			else:
				# 判断余额
				if float(param.total)>db_user.get('credit', 0.0):
					print '============================== -100'
					return json.dumps({'ret' : -100, 'msg' : '余额不足'})

				# 生成order_id
				order_id = app_helper.get_new_order_id(version)

				print 'new order_id', order_id
				
				# 生成新订单
				db_cart = db.app_user.find_one({'uname':uname['uname']},{'cart_order.%s'%param.session:1})
				new_order = dict(db_cart['cart_order'][param.session])
				new_order['order_id']=order_id
				new_order['status']='DUE'
				new_order['user_note']=param.note.strip()
				new_order['history']=[(app_helper.time_str(), uname['uname'], '提交余额支付')]

				ret_json = checkout(version, uname, {
					'session'   : param.session,
					'order_id'  : order_id,
					'shop_id'   : str(new_order['shop']),
					'addr_id'   : new_order['address'][0],
					'coupon_id' : new_order['coupon'][0] if float(new_order['coupon_disc'])>0 else '',
					'cart'      : json.dumps(new_order['cart']),
					'app_id'    : param.app_id,
					'use_credit': '1' if float(new_order.get('use_credit','0'))>0 else '', #2015-11-23
				})

				if ret_json['ret']<0:
					# checkout 出错
					return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

				if float(ret_json['data']['use_credit'])!=float(new_order['use_credit']):
					# checkout后金额有变化，说明库存或优惠券有变化
					print '============================== -100'
					return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单'})

				db.order_app.insert_one(new_order)
				return json.dumps({'ret' : 0, 'order_id' : order_id})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
