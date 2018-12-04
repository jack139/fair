#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/order_new')

# 新的订货单 ----------
class handler:   
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			#user_data=web.input(is_pack='1')

			# 查找
			db_shop = helper.get_shop_by_uid()
			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')
			
			return render.pos_order_new(helper.get_session_uname(), helper.get_privilege_name(), 
				db_shop2, helper.SHOP_TYPE)
		else:
			raise web.seeother('/')

	def POST(self): # 提交订货单，json返回
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			user_data=web.input(cart='')
			print user_data

			if user_data.cart=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()
			if db_shop==None:
				return json.dumps({'ret' : -1, 'msg' : '没有查到门店信息'})
			if db_shop['shop']=='':
				return json.dumps({'ret' : -1, 'msg' : '没有查到门店信息2'})

			#print user_data.cart
			cart = json.loads(user_data.cart)
			if len(cart)==0:
				return json.dumps({'ret' : -1, 'msg' : '无数据'})

			order = {
				'type'      : 'BOOK', # 订货单
				'status'    : 'WAIT',
				'shop_from' : '', # 发货点未知
				'shop_to'   : db_shop['shop'], # 收货店
				'cart'      : [],
				'history'   : [(helper.time_str(), helper.get_session_uname(), '建立订货单')]
			}

			# item = [ product_id, num, name, cost_price]
			# k - num 库存数量
			# u - num 称重
			for item in cart:
				new_item = {
					'product_id' : item[0],
					'num'        : round(float(item[1]),2) if item[0][2]=='2' else int(float(item[1])),
					'name'       : item[2],
					'cost_price' : item[3],
				}

				# 加入cart
				order['cart'].append(new_item)

			db.order_stock.insert_one(order)

			return json.dumps({ # 返回结果，
				'ret'  : 0,
				'data' : {  
					'cart_num' : len(order['cart']),
				}
			})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
