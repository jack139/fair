#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/plat/base_sku_json')

class handler:        #class PlatBaseSkuJson:
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			user_data=web.input(base_sku='')

			if user_data.base_sku=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			db_sku=db.base_sku.find_one({'_id':ObjectId(user_data['base_sku'])}, {
				'name'       : 1,
				'abstract'   : 1,
				#'ref_price'  : 1,
				#'min_price'  : 1,
				#'max_price'  : 1,
				'fresh_time' : 1,
				'original'   : 1,
				'available'  : 1,
				'image'      : 1,
			})
			if db_sku:
				return json.dumps({
					'ret'        : 0,
					'name'       : db_sku['name'],
					'abstract'   : db_sku['abstract'],
					#'ref_price'  : db_sku['ref_price'],
					#'min_price'  : db_sku['min_price'],
					#'max_price'  : db_sku['max_price'],
					'fresh_time' : db_sku['fresh_time'],
					'original'   : db_sku['original'],
					'available'  : db_sku['available'],
					'image'      : db_sku['image'],
				})
			else:
				return json.dumps({'ret' : -2, 'msg' : '无数据返回'})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})

