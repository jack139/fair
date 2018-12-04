#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/stock/order_view')

class handler:        #class StockOrderView:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'STOCK_ORDER'):
			render = helper.create_render(globals={'str':str})
			user_data=web.input(order='')

			if user_data.order=='':
				return render.info('错误的参数！')  
	
			# 查询工单信息
			db_order=db.order_stock.find_one({'_id':ObjectId(user_data.order)})
			if db_order==None:
				return render.info('order错误的参数！')  

			# 查询 站点信息
			db_shop2=db.base_shop.find({'_id':{'$in':[db_order['shop_from'], db_order['shop_to']]}}, 
				{'name':1, 'type':1})
			shops={}
			for s in db_shop2:
				shops[s['_id']]= '%s（%s）' % (s['name'].encode('utf-8'), helper.SHOP_TYPE[s['type']])

			db_shop3=db.base_shop.find({'type' : 'house'}, {'name':1, 'type':1})

			# 所有product_id
			p_id=[]
			for i in db_order['cart']:
				p_id.append(i['product_id'])

			# 查询 sku信息
			db_sku=db.sku_store.find({'product_id': {'$in':p_id}},
				{'product_id':1, 'unit':1, 'is_pack':1}) 
			skus={}
			for i in db_sku:
				skus[i['product_id']]=(
					i['is_pack'],
					helper.UNIT_TYPE[i['unit']],
				)

			next_status = None

			# 发货单
			if db_order['type']=='SEND': 
				# 简单处理阶段，直接到店
				if db_order['status']=='WAIT':
					next_status = 'ONSHOP'
			# 订货单
			elif db_order['type']=='BOOK': 
				if db_order['status']=='WAIT':
					next_status = 'ONSHOP'

			return render.stock_order_view(helper.get_session_uname(), helper.get_privilege_name(),
				db_order, skus, shops, helper.ORDER_STATUS, db_shop3, next_status, db_order['history'])
		else:
			raise web.seeother('/')

	def POST(self): # 发货处理
		if helper.logged(helper.PRIV_USER,'STOCK_ORDER'):
			render = helper.create_render()
			user_data=web.input(order='',order_type='', next_status='', shop_from='')

			if '' in (user_data.order, user_data.order_type, user_data.next_status, user_data.shop_from):
				return render.info('参数错误！')

			# 只处理等待发货的操作，其他不处理
			if user_data.next_status!='ONSHOP' or user_data.order_type not in ('SEND', 'BOOK'): #  确认发货
				return render.info('无需操作！','/stock/order')

			# 取得工单数据
			db_order = db.order_stock.find_one({'_id':ObjectId(user_data.order)},
				{'shop_from':1 , 'cart':1, 'status':1})

			if db_order==None:
				return render.info('未找到订单数据！')

			if db_order['status'] == user_data.next_status:
				return render.info('不能重复确认订单！')

			new_cart=[]
			for i in db_order['cart']:
				if i['product_id'][2] in ('1','3'):
					new_num = int(user_data[i['product_id']])
				else:
					new_num = round(float(user_data[i['product_id']]),2)

				# 从仓库库存中减库存，发送处理，目前仓库无库存，直接发货，所有不检查仓库库存
				'''
				r = db.inventory.find_one_and_update(
					{
						'product_id'  : i['product_id'],
						'shop'        : ObjectId(user_data.shop_from),
						'num'         : {'$gte' : new_num}
					},
					{ 
						'$inc'  : { 'num' : 0-new_num},
						'$push' : { 'history' : (helper.time_str(), 
							helper.get_session_uname(), '发货 %.2f ' % new_num)},
					},
					{'cost_price':1}
				)
				if r==None: # 应该不会发生，js已做检查
					return render.info('发货仓库库存不足: %s' % i['product_id'].encode('utf-8') )
				'''

				new_cart.append({
					'product_id' : i['product_id'],
					'num'        : i['num'],
					'send_num'   : new_num,
					'name'       : i['name'],
					'cost_price' : i['cost_price'],
				})

			# 工单在途数量增加
			db.order_stock.update_one({'_id' : ObjectId(user_data.order)}, {
				'$set':{
					'cart'       : new_cart,
					#'num_onroad' : db_order['num'], 
					'status'     : user_data.next_status,
					#'cost_price' : r['cost_price'], # 真实成本，从仓库库存成本来的
					'shop_from'  : ObjectId(user_data.shop_from), # 同一仓库发货！
				},
				'$push' : { 'history' : (helper.time_str(), 
					helper.get_session_uname(), '状态变为 %s' % user_data.next_status.encode('utf-8'))},
			})

			#return render.info('成功保存！','/stock/order')
			raise web.seeother('/stock/order_view?order='+user_data.order)
		else:
			raise web.seeother('/')
