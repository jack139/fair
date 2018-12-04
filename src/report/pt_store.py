#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/report/pt_store')

# SKU -------------------
class handler: # PlatSkuStore
	def GET(self):
		if helper.logged(helper.PRIV_USER,'REPORT_REPORT2'):
			render = helper.create_render()
			param=web.input(tuan_id='', status='', pt_order_id='')

			if param['tuan_id']!='': # 按tuan_id查活动订单
				condition = {'tuan_id':param['tuan_id']}
				if param['status']=='FAIL':
					condition['status'] = {'$in':['FAIL1', 'FAIL2', 'FAIL3']}
				elif param['status']!='':
					condition['status'] = param['status']

				r = db.pt_order.find(condition)
				return render.report_pt_order(helper.get_session_uname(), helper.get_privilege_name(), 
					r, helper.PT_REGION)
			elif param['pt_order_id']!='': # 按 pt_order_id 查活动订单详情
				r = db.pt_order.find_one({'pt_order_id':param['pt_order_id']})
				r2 = db.pt_store.find_one({'tuan_id':r['tuan_id']},{'title':1})
				return render.report_pt_order_detail(helper.get_session_uname(), helper.get_privilege_name(), 
					r, helper.PT_REGION, r2['title'])
			else: # 清单
				db_sku=db.pt_store.find({},{
					'tuan_id'     : 1,
					'title'       : 1,
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
						elif j['status'] in ['FAIL1', 'FAIL2', 'FAIL3']:
							fail1 += 1
					pt_orders[i['tuan_id']] = (succ1, open1, fail1)

					skus.append({
						'_id'         : i['_id'],
						'tuan_id'     : i['tuan_id'],
						'title'       : i['title'],
						'region_id'   : i['region_id'],
						'pt_orders'   : (succ1, open1, fail1),
					})
				
				return render.report_pt_store(helper.get_session_uname(), helper.get_privilege_name(), 
					skus, helper.PT_REGION)
		else:
		    raise web.seeother('/')
