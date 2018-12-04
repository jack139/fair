#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/base_sku')

class handler:   #class PlatBaseSku:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_BASE_SKU'):
			render = helper.create_render()

			skus=[]         
			db_sku=db.base_sku.find({},{
				'name'      : 1,
				'note'      : 1,
				'available' : 1,
				'image'     : 1,
				'original'  : 1,
			}).sort([('_id',1)])
			for u in db_sku:
				skus.append((u['_id'], u['name'], u['note'], u['available'],
					u['image'][0] if u.has_key('image') and len(u['image'])>0 else '',
					u['original'],
				))
			return render.base_sku(helper.get_session_uname(), helper.get_privilege_name(), skus)
		else:
		    raise web.seeother('/')