#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos_checkout')

# 购物车结算，json提交
class handler:        #class PosPosCheckout: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_POS'):
			user_data=web.input(cart='')

			if user_data.cart=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			#print user_data.cart
			cart = json.loads(user_data.cart)
			if len(cart)==0:
				return json.dumps({'ret' : -1, 'msg' : '无数据'})

			# 取得sku计数
			db_sa = db.user.find_one_and_update(
				{'uname'    : 'settings'},
				{'$inc'     : {'sa_count' : 1}},
				{'sa_count' : 1}
			)

			order = {
				'status'   : 'DUE',
				'shop'     : db_shop['shop'],
				'user'     : helper.get_session_uname(),
				'order_id' : 'f%06d' % db_sa['sa_count'],
				'cart'     : [],
				'cost'     : '0.00', # 成本合计
				'total'    : '0.00', # 价格小计
				'discount' : '0.00', # 折扣， 目前只去零（去分）
				'due'      : '0.00', # 应付价格
				'history'  : [(helper.time_str(), helper.get_session_uname(), '建立应付账单')]
			}

			# item = [ product_id, num, price]
			# k - num 库存数量
			# w - num 称重
			# u - num 称重
			for item in cart:
				r = db.inventory.find_one(  # 只检查库存sku是否存在，不检查数量，有可能负库存
					{
						'product_id'  : item[0],
						'shop'        : db_shop['shop'],
					},
					{'cost_price':1, 'ref_prod_id':1}
				)
				if r: # 如果库存数据中没此sku，会忽略掉，此情况应该不会发生
					new_item = {
						'product_id' : item[0],
						'num'        : item[1],
						'price'      : item[2],
						'name'       : item[3],
					}
					cost_price = r['cost_price']

					if item[0][0]=='w': # w-prod 信息都用 u-prod的替换
						new_item['product_id'] = r['ref_prod_id']
						new_item['w_id'] = item[0]
						# 查询成本, 从对应u-prod当前成本
						r2 = db.inventory.find_one({ # u-prod
							'shop'       : db_shop['shop'],
							'product_id' : r['ref_prod_id'],
						}, {'cost_price':1})
						cost_price = r2['cost_price']
					# 计算成本
					item_cost = round(float(item[1])*float(cost_price),2)
					new_item['cost'] = '%.2f' % item_cost

					# 加入cart
					order['cart'].append(new_item)

					# 累计售价和成本
					order['total'] = '%.2f' % (float(order['total'])+float(item[2]))
					order['cost'] = '%.2f' % (float(order['cost'])+item_cost)

			tt = float(order['total'])
			order['discount'] = '%.2f' % (tt - int(tt*10)/10.0) # 优惠掉分
			order['due'] = '%.2f' % (float(order['total'])-float(order['discount']))

			db.order_offline.insert_one(order)

			return json.dumps({ # 返回结果，实际有库存的结果，
				'ret'  : 0,
				'data' : {  
					'order_id' : order['order_id'],  
					'total'    : order['total'],
					'discount' : order['discount'],
					'due'      : order['due'],
					'cart_num' : len(order['cart']),
				}
			})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
