#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/invent_sku')

class handler:        #class PosInventSku:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_INVENTORY'):
			render = helper.create_render()
			user_data=web.input(product_id='')

			if user_data.product_id=='':
				return render.info('错误的参数！')  

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')

			db_invent=db.inventory.find_one({'product_id':user_data.product_id, 'shop':db_shop2['_id']})
			if db_invent:
				db_sku=db.sku_store.find_one({'_id':db_invent['sku']})
				if db_sku:
					base_sku=db.dereference(db_sku['base_sku'])
					return render.pos_invent_sku(helper.get_session_uname(), 
						helper.get_privilege_name(), 
						db_sku, 
						db_invent,
						helper.UNIT_TYPE[db_sku['unit']], 
						(base_sku['name'], base_sku['original'], 
						 base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else ''), 
						(str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]),
						user_data.product_id[0]=='w',
						helper.CATEGORY
					)
				else:
					return render.info('未查到sku！')
			else:
				return render.info('未查到库存！')
			
		else:
			raise web.seeother('/')

