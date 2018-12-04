#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos_pay')

# 付款／取消订单，json提交
class handler:        #class PosPosPay: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_POS'):
			user_data=web.input(order='', pay='')

			if '' in (user_data.order, user_data.pay):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 取得订单
			db_order = db.order_offline.find_one(
				{'order_id' : user_data.order, 'shop' : db_shop['shop']},
				{'status':1, 'cart':1, 'due':1}
			)
			if db_order==None:
				return json.dumps({'ret' : -1, 'msg' : '未找到订单！'})
			elif db_order['status']!='DUE':
				return json.dumps({'ret' : -1, 'msg' : '不是待付款订单！'})

			# 取消订单
			if user_data.pay=='cancel':
				db.order_offline.update_one({
						'order_id' : user_data.order,
						'shop'     : db_shop['shop'],
					},{
						'$set'  : { 'status':'CANCEL' },
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), '取消账单')},

					}
				)
				return json.dumps({'ret' : 0, 'msg' : '订单已取消！'})

			# 找零计算
			f_pay = float(user_data.pay)
			f_change = f_pay - float(db_order['due'])

			if f_change<0:
				return json.dumps({'ret' : -1, 'msg' : '付款金额不能小于应付总金额！'})

			# 减库存！
			# item = [ product_id, num, price]
			# k - num 库存数量
			# w - num 称重
			# u - num 称重
			for item in db_order['cart']:
				r = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
					{
						'product_id'  : item['product_id'],
						'shop'        : db_shop['shop'],
					},
					{ 
						'$inc'  : { 'num' : (-1 if item['product_id'][0]=='w' or item['product_id'][2] in ('1', '3') else -float(item['num']))},
						#'$push' : { 'history' : (helper.time_str(), 
						#	helper.get_session_uname(), '售出 %s' % str(item['num']))},
					},
					{'ref_prod_id':1, 'weight':1}
				)
				print r
				if r==None: # 不应该发生
					return json.dumps({'ret' : -1, 'msg' : '修改库存失败，请联系管理员！'})

				# 更新第3方库存 2015-10-10
				helper.elm_modify_num(db_shop['shop'], item['product_id'])

				# 称重项目，要去减 w-prod 的库存, cart里时u-prod
				if item.has_key('w_id'):
					# 减u=prodde库存
					db.inventory.update_one( # u-prod
						{
							'product_id' : item['w_id'],
							'shop'       : db_shop['shop'],
						},
						{ 
							'$inc'  : { 'num' : -1 },
							#'$push' : { 'history' : (helper.time_str(), 
							#	helper.get_session_uname(), '售出')},
						},
					)
			
			# 更新销货单信息
			db.order_offline.update_one({
					'order_id' : user_data.order,
					'shop'     : db_shop['shop'],
				},{
					'$set' : { 
						'status'    : 'PAID', 
						'pay'       : '%.2f' % f_pay,
						'change'    : '%.2f' % f_change,
						'paid_time' : helper.time_str(),
					},
					'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), '已付款')},

				}
			)

			return json.dumps({ # 返回结果，找零，
				'ret'  : 0, 
				'data' : {
					'due'      : db_order['due'],
					'pay'      : '%.2f' % f_pay,
					'change'   : '%.2f' % f_change,
				}
			})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
