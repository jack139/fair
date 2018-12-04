#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper, lbs

db = setting.db_web

url = ('/plat/base_shop_new')

class handler:        #class PlatBaseShopNew:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render()
			return render.base_shop_new(helper.get_session_uname(), 
				helper.get_privilege_name(),helper.SHOP_TYPE)
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render()
			user_data=web.input(shop_name='',shortname='',abstract='',available='1',
				address='',people='1',type='',worker=0,note='',app_shop='0',radius='2',poly='')

			if user_data.shop_name=='':
				return render.info('店名不能为空！')  

			if user_data.type=='':
				return render.info('门店类型不能为空！')  

			# 取得lbs坐标
			ret, loc0 = lbs.addr_to_loc(user_data['address'].encode('utf-8'))
			if ret<0:
				loc0 = {'lat': 0, 'lng': 0}

			# 取得多边形坐标
			#poly=user_data['poly'].encode('utf-8').split(',') # 地址信息
			#poly_xy=[]
			#if len(poly)>1:
			#	for i in poly:
			#		ret, loc = lbs.addr_to_loc(i)
			#		if ret<0:
			#			loc = (0,0)
			#		poly_xy.append((loc['lat'],loc['lng']))
			#	poly_xy.append(poly_xy[0])
			poly=user_data['poly'].encode('utf-8').split(';') # 已经是百度坐标
			poly_xy=[]
			if len(poly)>1:
				for i in poly:
					poly_xy.append(eval(i))
				poly_xy.append(poly_xy[0])

			db.base_shop.insert_one({
				'name'       : user_data['shop_name'],
				'shortname'  : user_data['shortname'],
				'abstract'   : user_data['abstract'],
				'address'    : user_data['address'],
				'loc'        : loc0,
				'people'     : user_data['people'],
				'type'       : user_data['type'],
				'available'  : int(user_data['available']),
				'worker'     : int(user_data['worker']),
				'image'      : user_data['image'].split(','),
				'note'       : user_data['note'],
				'refer'      : 0,
				'app_shop'   : int(user_data['app_shop']),
				'radius'     : int(user_data['radius']),
				'poly'       : user_data['poly'],
				'poly_xy'    : poly_xy,
				'history'    : [(helper.time_str(), helper.get_session_uname(), '新建')], # 纪录操作历史
			})
			db.base_image.update_many({'image':{'$in':user_data['image'].split(',')}},{'$inc':{'refer':1}})
			return render.info('成功保存！','/plat/base_shop')
		else:
			raise web.seeother('/')
