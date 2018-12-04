#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/pos/order_view')

class handler:        #class PosOrderView:        
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render(globals={'str':str})
			user_data=web.input(order='')

			if user_data.order=='':
				return render.info('错误的参数！')  

			# 查找所属shop
			db_shop = helper.get_shop_by_uid()

			# 查询工单信息
			db_order=db.order_stock.find_one({'_id' : ObjectId(user_data.order), '$or': [
				{'type' : 'SEND', 'shop_to' : db_shop['shop']},  # 发货单
				{'type' : 'BOOK', 'shop_to' : db_shop['shop']}  # 订货单
			]})
			if db_order==None:
				return render.info('order错误的参数！')  

			# 查询 站点信息
			db_shop2=db.base_shop.find({'_id':{'$in':[db_order['shop_from'], db_order['shop_to']]}}, 
				{'name':1, 'type':1})
			shops={}
			for s in db_shop2:
				shops[s['_id']]= '%s（%s）' % (s['name'].encode('utf-8'), helper.SHOP_TYPE[s['type']])

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
				if db_order['status']=='ONSHOP':
					next_status = 'CONFIRM'
			# 订货单
			elif db_order['type']=='BOOK': 
				if db_order['status']=='ONSHOP':
					next_status = 'CONFIRM'

			return render.pos_order_view(helper.get_session_uname(), helper.get_privilege_name(),
				db_order, skus, shops, helper.ORDER_STATUS, next_status, db_order['history'])
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			user_data=web.input(order='',order_type='', next_status='')

			if '' in (user_data.order, user_data.order_type, user_data.next_status):
				return render.info('参数错误！')

			# 查找所属shop
			db_shop = helper.get_shop_by_uid()

			# 只处理确认收货的操作，其他不处理
			if user_data.next_status!='CONFIRM' or user_data.order_type not in ('SEND', 'BOOK'): # 确认收货
				return render.info('无需操作！','/pos/order')

			# 取得工单数据
			db_order = db.order_stock.find_one({
				'_id'     : ObjectId(user_data.order),
				'shop_to' : db_shop['shop']	
			}, {'shop_to' : 1 , 'cart' : 1, 'status' : 1})

			if db_order==None:
				return render.info('未找到订单数据！')

			if db_order['status'] == user_data.next_status:
				return render.info('不能重复确认订单！')

			new_cart=[]
			for i in db_order['cart']:
				# 增加门店库存
				#new_num = round(float(i['num']), 2)
				if i['product_id'][2] in ('1','3'):
					new_num = int(user_data['recv_'+i['product_id']])
				else:
					new_num = round(float(user_data['recv_'+i['product_id']]), 2)
				r = db.inventory.find_one_and_update(
					{
						'product_id'  : i['product_id'],
						'shop'        : db_order['shop_to'],
					},
					{ 
						'$inc'  : { 'num' : new_num},
						#'$set'  : { 'cost_price' : '%.2f' % avg_price},
						'$push' : { 'history' : (helper.time_str(), 
							helper.get_session_uname(), '收货 %.2f ' % new_num)},
					},
					{'num':1, 'cost_price':1}
				)

				# 更新第3方库存 2015-10-10
				helper.elm_modify_num(db_order['shop_to'], i['product_id'])

				if r==None: # 门店新sku
					db_sku = db.sku_store.find_one({
							'product_id':i['product_id']
						}, {
							'ref_price'   : 1,
							'list_in_app' : 1,
							'sort_weight' : 1, 
							'category'    : 1, 
							'available'   : 1, 
					})
					db.inventory.insert_one({
						'sku'        : db_sku['_id'],
						'shop'       : db_order['shop_to'],
						'product_id' : i['product_id'],
						'price'      : db_sku['ref_price'],
						'cost_price' : i['cost_price'], 
						'weight'     : 0,
						'online'     : db_sku['available'],
						'num'        : new_num,
						'audit'      : -1,
						'list_in_app': db_sku['list_in_app'],
						'sort_weight': db_sku['sort_weight'], 
						'category'   : db_sku['category'],
						'history'    : [(helper.time_str(), 
							helper.get_session_uname(), '新建库存 %.2f' % new_num)], # 纪录操作历史
					})
					#return render.info('未找到库存数据！')
				else:
					# 计算新的评价价格 （移动平均价）
					# 注意：虽然与上面update不是原子操作，但不会导致价格计算不精确
					sum_num = r['num'] + new_num
					sum_price = float(r['cost_price'])*r['num']+float(i['cost_price'])*new_num
					if sum_num<=0: # 新库存可能为零， 为零或负库存时，不修改移动评价价 2015-08-26
						avg_price = float(r['cost_price'])
					else:
						avg_price = sum_price / sum_num

					# 新成本价格更新到db
					db.inventory.update_one({
						'product_id'  : i['product_id'],
						'shop'        : db_order['shop_to'],
					}, {'$set' : {'cost_price' : '%.2f' % avg_price}})

				new_cart.append({
					'product_id' : i['product_id'],
					'num'        : i['num'],
					'send_num'   : i['send_num'],
					'recv_num'   : new_num,
					'name'       : i['name'],
					'cost_price' : i['cost_price'],
				})

			# 工单在途数量清零
			db.order_stock.update_one({'_id' : ObjectId(user_data.order)}, {
				'$set':{
					'cart'         : new_cart,
					#'num_onroad'   : 0, 
					'status'       : user_data.next_status,
					'confirm_time' : helper.time_str(), # 确认收货时间，方便盘点
				},
				'$push' : { 'history' : (helper.time_str(), 
					helper.get_session_uname(), '状态变为 %s' % user_data.next_status.encode('utf-8'))},
			})

			#return render.info('成功保存！','/pos/order')
			raise web.seeother('/pos/order_view?order='+user_data.order)
		else:
			raise web.seeother('/')
