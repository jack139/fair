#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper, lbs

db = setting.db_web

url = ('/plat/base_shop_edit')

class handler:        #class PlatBaseShopEdit:        
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render(globals={'str':str})
			user_data=web.input(base_shop='')

			if user_data.base_shop=='':
				return render.info('错误的参数！')  
	
			db_shop=db.base_shop.find_one({'_id':ObjectId(user_data.base_shop)})
			if db_shop!=None:
				return render.base_shop_edit(helper.get_session_uname(), helper.get_privilege_name(),
					db_shop, helper.SHOP_TYPE)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render()
			user_data=web.input(base_shop='', shop_name='',shortname='',abstract='',available='1',
				address='',people='1',type='',worker=0,note='',app_shop='0',radius='2')
			#print user_data

			if user_data.shop_name=='':
				return render.info('店名不能为空！')  

			if user_data.type=='':
				return render.info('门店类型不能为空！')  

			# 取得lbs坐标
			ret, loc0 = lbs.addr_to_loc(user_data['address'].encode('utf-8'))
			if ret<0:
				loc0 = {'lat': 0, 'lng': 0}

			# 取得多边形坐标
			#poly=user_data['poly'].encode('utf-8').split(',')
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


			db.base_shop.update_one({'_id':ObjectId(user_data['base_shop'])}, {'$set':{
				'name'       : user_data['shop_name'],
				'shortname'  : user_data['shortname'],
				'abstract'   : user_data['abstract'],
				'address'    : user_data['address'],
				'loc'        : loc0,
				'people'     : user_data['people'],
				'type'       : user_data['type'],
				'available'  : int(user_data['available']),
				'worker'     : int(user_data['worker']),
				#'image'      : user_data['image'].split(','),
				'app_shop'   : int(user_data['app_shop']),
				'radius'     : int(user_data['radius']),
				'poly'       : user_data['poly'],
				'poly_xy'    : poly_xy,
				'note'       : user_data['note'],
			}})
			
			db.base_shop.update_one({'_id':ObjectId(user_data['base_shop'])}, {'$push':{
				'history' : (helper.time_str(), helper.get_session_uname(), '修改'), # 纪录操作历史
			}})

			return render.info('成功保存！','/plat/base_shop')
		else:
			raise web.seeother('/')
