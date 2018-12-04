#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos_json2')

# 返回指定sku的信息，用于 订货
# 与 销货 不同，此处返回sku_store里的信息，有可能本地无库存
class handler:      
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			user_data=web.input(product_id='')

			if user_data.product_id=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 查sku商品信息
			db_sku=db.sku_store.find_one({'product_id' : user_data.product_id})
			if not db_sku:
				return json.dumps({'ret' : -1, 'msg' : '未查到商品信息！'})

			# 查base_sku
			base_sku=db.dereference(db_sku['base_sku'])

			# 返回结果
			ret = {'ret': 0, 'data':{
				'product_id'   : db_sku['product_id'],
				'name'         : base_sku['name'],
				'unit_name'    : helper.UNIT_TYPE[db_sku['unit']],
				'is_pack'      : db_sku['is_pack'],
				'cost_price'   : db_sku['ref_cost'],
			}}

			return json.dumps(ret)
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})

