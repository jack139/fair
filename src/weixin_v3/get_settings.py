#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/get_settings')

# 获取全局参数
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='',session_id='')

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)
		if uname:
			db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

			print 'http://%s/image/product' % setting.image_host

			# 返回全局参数
			return json.dumps({'ret' : 0, 'data' : {
				'delivery_fee'  : '%.2f' % app_helper.delivery_fee, # v3
				'free_delivery' : '%.2f' % app_helper.free_delivery,
				'first_promote' : '%.2f' % app_helper.first_promote,
				'cod_enable'    : False,
				#'image_host'    : '/static/image/product',
				'image_host2'   : 'http://%s/image/product' % setting.image_host,
				'category'      : app_helper.CATEGORY2_WX, # v3
				#'banner'        : ['/banner20151019_1.jpg','/banner20151018_2.jpg','/banner20151016_3.jpg'],
				'banner'        : app_helper.BANNER_WX, # v3
				'banner_url'    : app_helper.BANNER_URL_WX, #v3
				'default_shop'  : setting.default_shop, # 返回默认站店
				'default_name'  : db_shop['name'] if db_shop else '',
				'phone_number'  : uname['uname'],
			}})
		else:
			print '无效登录'
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
