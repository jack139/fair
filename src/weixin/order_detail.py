#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, helper

db = setting.db_web

url = ('/wx/order_detail')

# 取消订单
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', order_id='')

		if param.order_id=='':
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

			# 获得订单
			#print param.order_id, uname
			db_order = db.order_app.find_one({'order_id' : param.order_id, 'user':{'$in':uname.values()}})
			if db_order==None:
				return json.dumps({'ret' : -3, 'msg' : '未找到订单！'})

			cart=[]
			for i in db_order['cart']:
				r = db.sku_store.find_one({'product_id':i['product_id']},
					{'base_sku':1})
				base_sku = db.dereference(r['base_sku'])
				image = base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else ''
				cart.append({
					'product_id' : i['product_id'],
					'title'      : i['title'],
					'price'      : i['price'],
					'num2'       : i['num2'],
					'image'      : '/%s/%s' % (image[:2], image),
				})

			data={
				'order_id'     : db_order['order_id'],
				'shop_id'      : str(db_order['shop']), # 需要中文名
				'status'       : helper.ORDER_STATUS['APP'].get(db_order['status'],'未知状态'),  # 需要中文名
				'deadline'     : db_order['deadline']-int(time.time()), # 离支付截至的时间,秒数
				'delivery'     : {
					'addr_id'     : db_order['address'][0],
					'address'     : db_order['address'][3],
					'contact'     : db_order['address'][1],
					'contact_tel' : db_order['address'][2],
					'runner'      : db_order['runner']['name'] if db_order.has_key('runner') else '', # 送货员姓名
					'runner_tel'  : db_order['runner']['tel'] if db_order.has_key('runner') else '', # 送货员电话
				}, 
				'cart'         : cart,
				'total'        : db_order['total'],
				'coupon'       : db_order['coupon'][0] if db_order['coupon'] else '',
				'coupon_disc'  : db_order['coupon_disc'],
				'first_disc'   : db_order['first_disc'],
				'delivery_fee' : db_order['delivery_fee'],
				'due'          : db_order['due'],
				'star'         : db_order.get('star', 1),
				'credit'       : '%.2f' % db_user.get('credit', 0.0),
			}

			return json.dumps({'ret' : 0, 'data' : data})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
