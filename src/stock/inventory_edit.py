#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/stock/inventory_edit')

class handler:        #class StockInventoryEdit:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'STOCK_INVENTORY'):
			render = helper.create_render()
			user_data=web.input(sku='')

			if user_data.sku=='':
				return render.info('错误的参数！')  
	
			db_sku=db.sku_store.find_one({'_id':ObjectId(user_data.sku)})
			if db_sku!=None:
				db_shop=db.base_shop.find({'available':1}, {'name':1,'type':1})
				shops = []
				for s in db_shop:
					shops.append((s['_id'], s['name'], helper.SHOP_TYPE[s['type']]))
				base_sku=db.dereference(db_sku['base_sku'])
				return render.stock_invent_edit(helper.get_session_uname(), 
					helper.get_privilege_name(), db_sku, 
					{'name' : base_sku['name'],'original' : base_sku['original']}, 
					helper.UNIT_TYPE, shops)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self): # 从whouse给shop补货,商品sku数量num，ajax调用，返回json
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'STOCK_INVENTORY'):
			user_data=web.input(sku='', shop='', num='', whouse='')

			if '' in (user_data.sku, user_data.shop, user_data.num, user_data.whouse):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})
			
			# 检查sku合法性
			db_sku = db.sku_store.find_one({'_id':ObjectId(user_data.sku)},{
				'product_id'  : 1,
				'ref_price'   : 1,
				'ref_cost'    : 1,
				'list_in_app' : 1,
				'sort_weight' : 1, 
				'category'    : 1, 
				'available'   : 1, 
			})
			if not db_sku:
				return json.dumps({'ret' : -1, 'msg' : 'sku参数错误'})

			#先检查库存记录是否已存在
			db_old = db.inventory.find_one({'sku':ObjectId(user_data.sku),'shop':ObjectId(user_data.shop)},{'num':1})
			if not db_old:
				# 新的库存记录
				db.inventory.insert_one({
					'sku'        : ObjectId(user_data.sku),
					'shop'       : ObjectId(user_data.shop),
					'product_id' : db_sku['product_id'],
					'price'      : db_sku['ref_price'],
					'cost_price' : db_sku['ref_cost'], # 参考成本
					'weight'     : 0,
					'online'     : db_sku['available'],
					'num'        : 0,
					'audit'      : -1,
					'list_in_app': db_sku['list_in_app'],
					'sort_weight': db_sku['sort_weight'], 
					'category'   : db_sku['category'],
					'history'    : [(helper.time_str(), helper.get_session_uname(), '新建库存 0')], # 纪录操作历史
				})
			
			# 生成发货单
			if int(user_data.num)>0:
				db.order_stock.insert_one({
					"type"       : 'SEND',
					"status"     : "WAIT",
					"shop_to"    : ObjectId(user_data.shop),
					"shop_from"  : ObjectId(user_data.whouse),
					"product_id" : db_sku['product_id'],
					"cost_price" : db_sku['ref_cost'], # 参考成本，不一定是真实成本
					"num"        : int(user_data.num),
					"num_onroad" : 0, # 在途数量
					'history'    : [(helper.time_str(), helper.get_session_uname(), '状态为 WAIT')], # 纪录操作历史
				})
				return json.dumps({'ret' : 0, 'msg' : '已生成发货单。'})
			else:
				return json.dumps({'ret' : 0, 'msg' : '补货数量为0，未生成新发货单。'})	
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
