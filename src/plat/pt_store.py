#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/pt_store')

# SKU -------------------
class handler: # PlatSkuStore
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_PT_STORE'):
			render = helper.create_render()

			db_sku=db.pt_store.find({},{
				'tuan_id'     : 1,
				'title'       : 1,
				'expire_time' : 1,
				'online'      : 1,
				'sale_out'    : 1,
				'tuan_size'   : 1,
				'region_id'   : 1,
			}).sort([('_id',1)])

			pt_orders = {}
			skus = []
			for i in db_sku:
				r = db.pt_order.find({'tuan_id':i['tuan_id']},{'status':1})
				succ1 = open1 = fail1 = 0
				for j in r:
					if j['status']=='OPEN':
						open1 += 1
					elif j['status']=='SUCC':
						succ1 += 1
					elif j['status'] in ['FAIL1', 'FAIL2']:
						fail1 += 1
				pt_orders[i['tuan_id']] = (succ1, open1, fail1)

				skus.append({
					'_id'         : i['_id'],
					'tuan_id'     : i['tuan_id'],
					'title'       : i['title'],
					'expire_time' : i['expire_time'],
					'online'      : i['online'],
					'sale_out'    : i['sale_out'],
					'tuan_size'   : i['tuan_size'],
					'region_id'   : i['region_id'],
					'pt_orders'   : (succ1, open1, fail1),
				})
			
			return render.pt_store(helper.get_session_uname(), helper.get_privilege_name(), 
				skus, helper.PT_REGION)
		else:
		    raise web.seeother('/')
