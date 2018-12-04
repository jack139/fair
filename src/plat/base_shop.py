#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/base_shop')

class handler:        #class PlatBaseShop:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SHOP'):
			render = helper.create_render()

			shops=[]  
			db_shop=db.base_shop.find({},{'name':1,'note':1,'available':1,'image':1,'type':1}).sort([('_id',1)])
			for u in db_shop:
				shops.append((u['_id'], u['name'], u['note'], u['available'], 
					u['image'][0] if u.has_key('image') and len(u['image'])>0 else '',
					helper.SHOP_TYPE[u['type']]
				))
			return render.base_shop(helper.get_session_uname(), helper.get_privilege_name(), shops)
		else:
			raise web.seeother('/')
