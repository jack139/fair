#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/plat/base_sku_edit')

class handler:  #class PlatBaseSkuEdit:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			render = helper.create_render()
			user_data=web.input(base_sku='')

			if user_data.base_sku=='':
				return render.info('错误的参数！')  
	
			db_sku=db.base_sku.find_one({'_id':ObjectId(user_data.base_sku)})
			if db_sku!=None:
				return render.base_sku_edit(helper.get_session_uname(), 
					helper.get_privilege_name(), db_sku)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			render = helper.create_render()
			user_data=web.input(base_sku='', sku_name='',abstract='', available=1,
				fresh_time=0,original='',note='')
			#print 'image: ', user_data.image

			if user_data.sku_name=='':
				return render.info('品名不能为空！')  

			update_set = {
				'name'       : user_data['sku_name'],
				'abstract'   : user_data['abstract'],
				#'ref_price'  : '%.2f' % float(user_data['ref_price']),
				#'min_price'  : '%.2f' % float(user_data['min_price']),
				#'max_price'  : '%.2f' % float(user_data['max_price']),
				'fresh_time' : int(user_data['fresh_time']),
				#'image'      : user_data['image'].split(','),
				'original'   : user_data['original'],
				'available'  : int(user_data['available']),
				'note'       : user_data['note'],
			}
			# 如果没有更新图片，就不更新图片 2015-09-04
			if len(user_data['image'].strip())>0:
				update_set['image'] = user_data['image'].split(',')
			#print update_set
			db.base_sku.update_one({'_id':ObjectId(user_data['base_sku'])}, {'$set':update_set})
			
			db.base_sku.update_one({'_id':ObjectId(user_data['base_sku'])}, {'$push':{
				'history' : (helper.time_str(), helper.get_session_uname(), '修改'), # 纪录操作历史
			}})

			return render.info('成功保存！','/plat/base_sku')
		else:
			raise web.seeother('/')
