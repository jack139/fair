#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
from bson.objectid import ObjectId
import helper

db = setting.db_web

url = ('/plat/base_shop_map')

class handler:        #class PlatBaseShop:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render(plain=True)

			db_shop=db.base_shop.find({'type':{'$in':['chain','store','dark','counter']}},{
				'name'    : 1,
				'type'    : 1,
				'poly'    : 1,
				'poly_xy' : 1,
				'app_shop': 1,
			}).sort([('_id',1)])

			data=[]
			for i in db_shop:
				data.append({
					'id'      : i['_id'],
					'name'    : i['name'],
					'poly'    : i.get('poly',''),
					'poly_xy' : i.get('poly_xy',[]),
					'app_shop': i.get('app_shop',0)
				})
			return render.map_shops(helper.get_session_uname(), helper.get_privilege_name(), data)
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render()
			user_data=web.input()
			
			for d in user_data.keys():
				if d[:4]=='poly' and len(user_data[d])>0:
					print d, user_data[d]
					poly=user_data[d].encode('utf-8').split(';') # 已经是百度坐标
					poly_xy=[]
					if len(poly)>1:
						for i in poly:
							poly_xy.append(eval(i))
						poly_xy.append(poly_xy[0])

					db.base_shop.update_one({'_id':ObjectId(d[5:])}, {'$set':{
						'poly' : user_data[d],
						'poly_xy' : poly_xy,
					}})

			return render.info('保存成功！','/plat/base_shop')  
		else:
			raise web.seeother('/')
