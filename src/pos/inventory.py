#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, re
from config import setting
import helper

db = setting.db_web

url = ('/pos/inventory')

# 店内库存
class handler:        #class PosInventory:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_INVENTORY'):
			render = helper.create_render()
			user_data=web.input(is_pack='k', show='1')

			is_pack = user_data['is_pack']

			# 分3类： u－散称sku， k－包装sku，w-已称重sku
			if is_pack not in ('k', 'u', 'w'):
				return render.info('错误的参数！')

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
			if is_pack=='w':
				condition['product_id'] = { '$regex' : 'w.*', '$options' : 'i' }
				if user_data.show=='1': # 显示有库存的
					condition['num']={'$gt' : 0}
				else:             # 显示已售出的
					condition['num']={'$lte' : 0}

			db_invent = db.inventory.find(condition, {
				'sku'        : 1, 
				'online'     : 1, 
				'list_in_app': 1,
				'category'   : 1,
				'price'      : 1,
				'cost_price' : 1, 
				'weight'     : 1, 
				'total'      : 1, 
				'product_id' : 1, 
				'num'        : 1,
				'pre_pay_num': 1,
			}).sort([('product_id',1)])

			invent = []
			skus = []
			for s in db_invent:
				skus.append(s['sku'])
				invent.append((
					s['sku'],  #0
					(s['online'],s.get('list_in_app',0),s.get('category','001')),   #1
					(s['price'],s['cost_price']),   #2
					s['weight'],  #3
					s.get('total', ''),   #4
					s['product_id'], #5
					(s['num'], s.get('pre_pay_num',0)), #6
				))  

			# 包装的、有效的sku
			db_sku=db.sku_store.find({'_id':{'$in':skus}} ,{
				'product_id' : 1,
				'base_sku'   : 1,
				'note'       : 1,
				#'online'     : 1,
				'is_pack'    : 1,
				'unit'       : 1,
				#'unit_num'   : 1,
				'ref_price'  : 1,
				'app_title'  : 1 
			}).sort([('_id',1)])

			skus = {}
			for u in db_sku:
				base_sku = db.dereference(u['base_sku'])

				skus[u['_id']]=(
					base_sku['name'] if len(u['app_title'].strip())==0 else u['app_title'],   #7
					u['note'],  #8
					base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
					'',  #10 
					helper.UNIT_TYPE[u['unit']],   #11
					u['is_pack'],   #12
					u['ref_price'],   #13
					base_sku['original'],   #14
				)

			data = []
			for i in invent:
				# 准备数据
				data.append(i + skus[i[0]])

			return render.pos_invent(helper.get_session_uname(), helper.get_privilege_name(), data,
				 (str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]),
				 is_pack, helper.CATEGORY, user_data.show)
		else:
			raise web.seeother('/')
