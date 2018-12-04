#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/sku_store')

# SKU -------------------
class handler: # PlatSkuStore
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
			render = helper.create_render()

			skus=[]         
			db_sku=db.sku_store.find({},{
				'product_id' : 1,
				'base_sku'   : 1,
				'note'       : 1,
				'available'  : 1,
				'is_pack'    : 1,
				'unit'       : 1,
				#'unit_num'   : 1,
				'ref_price'  : 1,
				'ref_cost'   : 1,
				'list_in_app': 1,
				'app_title'  : 1,
			}).sort([('_id',1)])
			
			for u in db_sku:
				base_sku = db.dereference(u['base_sku'])

				# 准备数据
				skus.append((u['_id'], 
					base_sku['name'] if len(u['app_title'].strip())==0 else u['app_title'], 
					u['note'], u['available'],
					base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
					'', helper.UNIT_TYPE[u['unit']], 
					u['is_pack'], u['ref_price'], u['product_id'], u['ref_cost'],
					u['list_in_app']
				))
			return render.sku_store(helper.get_session_uname(), helper.get_privilege_name(), skus)
		else:
		    raise web.seeother('/')
