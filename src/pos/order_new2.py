#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, re
from config import setting
import helper

db = setting.db_web

url = ('/pos/order_new2')

# 新订货单，按库存商品清单格式
class handler:        
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			user_data=web.input()

			# 查找
			db_shop = helper.get_shop_by_uid()
			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')
			
			# 查找所属店铺库存 包装库存
			# 模糊查询，以k开头 {'$regex':'k.*','$options': 'i'}
			condition = {
				'shop'       : db_shop['shop'],
				'product_id' : { '$not': re.compile('^w.*') },
			}

			db_invent = db.inventory.find(condition, {
				'sku'        : 1, 
				'online'     : 1, 
				#'price'      : 1,
				#'cost_price' : 1, 
				#'weight'     : 1, 
				#'total'      : 1, 
				'product_id' : 1, 
				'num'        : 1
			}).sort([('product_id',1)])

			invent = []
			skus = []
			for s in db_invent:
				skus.append(s['sku'])
				invent.append((
					s['sku'],  #0
					s['online'],   #1
					#(s['price'], s['cost_price']),   
					#s['weight'],  
					#s['total'] if s.has_key('total') else '',   
					s['product_id'], #2
					s['num'], #3
				))  

			# 包装的、有效的sku
			db_sku=db.sku_store.find({'_id':{'$in':skus}} ,{
				'product_id' : 1,
				'base_sku'   : 1,
				#'note'       : 1,
				#'online'     : 1,
				'is_pack'    : 1,
				'unit'       : 1,
				#'unit_num'   : 1,
				#'ref_price'  : 1,
				'app_title'  : 1,
				'ref_cost'   : 1
			}).sort([('_id',1)])

			skus = {}
			for u in db_sku:
				base_sku = db.dereference(u['base_sku'])

				skus[u['_id']]=(
					base_sku['name'] if len(u['app_title'].strip())==0 else u['app_title'],   #4
					#u['note'],  #
					#base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
					#'',  #
					helper.UNIT_TYPE[u['unit']],   #5
					u['is_pack'],   #6
					u['ref_cost'],   #7
					base_sku['original'],   #8
				)

			data = []
			for i in invent:
				# 准备数据
				data.append(i + skus[i[0]])

			return render.pos_order_new2(helper.get_session_uname(), helper.get_privilege_name(), data,
				 (str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]))
		else:
			raise web.seeother('/')
