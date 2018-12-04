#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/get_settings')

# 获取全局参数
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', secret='', sign='')

		if '' in (param.app_id, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

		# 返回全局参数
		return json.dumps({'ret' : 0, 'data' : {
			'free_delivery' : '%.2f' % app_helper.free_delivery,
			'first_promote' : '%.2f' % app_helper.first_promote,
			'cod_enable'    : False,
			'image_host'    : '/static/image/product',
			'image_host2'   : 'http://app.urfresh.cn/static/image/product',
			'banner'        : app_helper.BANNER['c001'],
			'default_shop'  : setting.default_shop, # 返回默认站店
			'default_name'  : db_shop['name'] if db_shop else '',
			'app_store'     : 'no',
		}})
