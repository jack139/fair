#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/plat/pt_store_edit')

class handler:  #class PlatBaseSkuEdit:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_PT_STORE'):
			render = helper.create_render()
			user_data=web.input(sku='')

			if user_data.sku=='':
				return render.info('错误的参数！')  
	
			db_sku=db.pt_store.find_one({'_id':ObjectId(user_data.sku)})
			if db_sku!=None:
				return render.pt_store_edit(helper.get_session_uname(), 
					helper.get_privilege_name(), db_sku, helper.PT_REGION)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_PT_STORE'):
			render = helper.create_render()
			user_data=web.input(region_id=[],title='', tuan_size='',
				price='',tuan_price='',ref_price='', shop_online=[])

			if '' in (user_data.title, user_data.tuan_size, user_data.price, 
				user_data.tuan_price, user_data.ref_price):
				return render.info('必填参数不能为空！')  

			if user_data.region_id==[]:
				return render.info('区域参数不能为空！') 				

			update_set = {
				'region_id'  : user_data['region_id'],
				'title'      : user_data['title'],
				'desc'       : user_data['desc'],
				'tuan_size'  : int(user_data['tuan_size']),
				'price'      : '%.2f' % float(user_data['price']),
				'tuan_price' : '%.2f' % float(user_data['tuan_price']),
				'ref_price'  : '%.2f' % float(user_data['ref_price']),
				'expire_time': user_data['expire_time'],
				'expire_tick': int(time.mktime(time.strptime(user_data['expire_time'],"%Y-%m-%d")))+3600*24,
				'promote'    : int(user_data['promote']),
				'sale_out'   : int(user_data['sale_out']),
				'sort_weight': int(user_data['sort_weight']),
				'note'       : user_data['note'],
				'online'     : user_data['shop_online'],
			}
			# 如果没有更新图片，就不更新图片 2015-09-04
			if len(user_data['image'].strip())>0:
				update_set['image'] = user_data['image'].split(',')
			#print update_set
			db.pt_store.update_one({'tuan_id':user_data['tuan_id']}, {
				'$set'  : update_set,
				'$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改')},
			})
			
			return render.info('成功保存！','/plat/pt_store')
		else:
			raise web.seeother('/')
