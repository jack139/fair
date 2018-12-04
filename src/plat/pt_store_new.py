#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time, random
from config import setting
import helper

db = setting.db_web

url = ('/plat/pt_store_new')

class handler:        #class PlatBaseSkuNew:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_PT_STORE'):
			render = helper.create_render()
			return render.pt_store_new(helper.get_session_uname(), helper.get_privilege_name(),
				helper.PT_REGION)
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

			db.pt_store.insert_one({
				'region_id'  : user_data['region_id'],
				'tuan_id'    : 't%s%s' % (helper.time_str(format=2)[2:],helper.my_rand(5)),
				'title'      : user_data['title'],
				'desc'       : user_data['desc'],
				'tuan_size'  : int(user_data['tuan_size']),
				'price'      : '%.2f' % float(user_data['price']),
				'tuan_price' : '%.2f' % float(user_data['tuan_price']),
				'ref_price'  : '%.2f' % float(user_data['ref_price']),
				'expire_time': user_data['expire_time'],
				'expire_tick': int(time.mktime(time.strptime(user_data['expire_time'],"%Y-%m-%d")))+3600*24,
				'volume'     : random.randint(150,200),
				'promote'    : int(user_data['promote']),
				'sale_out'   : int(user_data['sale_out']),
				'sort_weight': int(user_data['sort_weight']),
				'image'      : user_data['image'].split(','),
				'note'       : user_data['note'],
				'online'     : user_data['shop_online'],
				'history'    : [(helper.time_str(), helper.get_session_uname(), '新建活动')], # 纪录操作历史
			})
			db.base_image.update_many({'image':{'$in':user_data['image'].split(',')}},{'$inc':{'refer':1}})
			return render.info('成功保存！','/plat/pt_store')
		else:
			raise web.seeother('/')
