#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/base_sku_new')

class handler:        #class PlatBaseSkuNew:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			render = helper.create_render()
			return render.base_sku_new(helper.get_session_uname(), helper.get_privilege_name())
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			render = helper.create_render()
			user_data=web.input(sku_name='',abstract='', available=1,
				fresh_time=0,original='',note='')

			if user_data.sku_name=='':
				return render.info('品名不能为空！')  

			db.base_sku.insert_one({
				'name'       : user_data['sku_name'],
				'abstract'   : user_data['abstract'],
				#'ref_price'  : '%.2f' % float(user_data['ref_price']),
				#'min_price'  : '%.2f' % float(user_data['min_price']),
				#'max_price'  : '%.2f' % float(user_data['max_price']),
				'fresh_time' : int(user_data['fresh_time']),
				'original'   : user_data['original'],
				'available'  : int(user_data['available']),
				'image'      : user_data['image'].split(','),
				'note'       : user_data['note'],
				'refer'      : 0,
				'history'    : [(helper.time_str(), helper.get_session_uname(), '新建')], # 纪录操作历史
			})
			db.base_image.update_many({'image':{'$in':user_data['image'].split(',')}},{'$inc':{'refer':1}})
			return render.info('成功保存！','/plat/base_sku')
		else:
			raise web.seeother('/')
