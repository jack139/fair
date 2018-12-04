#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, re
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos_product_id')

# 模糊查询product_id
class handler:        
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			user_data=web.input(product_id='')

			if user_data.product_id=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			#db_shop = helper.get_shop_by_uid()

			# 查库存信息
			db_id=db.sku_store.find({
				'product_id' : re.compile('%s$' % user_data.product_id.strip()),
			}, {'product_id':1})
			if db_id.count()==0:
				return json.dumps({'ret' : -1, 'msg' : '未查到商品！'})
			elif db_id.count()>1:
				return json.dumps({'ret' : -2, 'msg' : '查到多个商品，请重新输入！'})

			return json.dumps({'ret': 0, 'data':{
				'product_id' : db_id[0]['product_id'],
			}})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})

