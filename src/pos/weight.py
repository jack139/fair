#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/weight')

# POS称重 -------------------
class handler:        #class PosWeight:
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()

			# 查找
			db_shop = helper.get_shop_by_uid()
			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')
			# 查找所属店铺库存
			db_invent = db.inventory.find({
				'product_id' : { '$not': re.compile('^w.*') },
				'shop'       : db_shop['shop'],
			},{'sku':1, 'online':1, 'price':1, 'product_id':1})
			invent = {}
			for s in db_invent:
				if s['product_id'][2] in ('1','3'): # 只记录散进散出
					continue
				invent[s['sku']]=(s['online'], s['price'])
			
			# 散装、有效的sku
			db_sku=db.sku_store.find({'_id':{'$in':invent.keys()}},{
				'product_id' : 1,
				'base_sku'   : 1,
				'note'       : 1,
				#'online'     : 1,
				'is_pack'    : 1,
				'unit'       : 1,
				#'unit_num'   : 1,
				#'ref_price'  : 1,
			}).sort([('_id',1)])

			skus=[]			
			for u in db_sku:
				base_sku = db.dereference(u['base_sku'])

				# 准备数据
				skus.append((u['_id'], base_sku['name'], u['note'], invent[u['_id']][0],
					base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
					'', helper.UNIT_TYPE[u['unit']], 
					u['is_pack'], invent[u['_id']][1], u['product_id'],
				))
			return render.weight(helper.get_session_uname(), helper.get_privilege_name(), skus,
				 (str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]))
		else:
			raise web.seeother('/')
