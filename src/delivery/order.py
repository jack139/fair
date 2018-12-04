#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/delivery/order')

# 快递员 之 工单处理 -------------------
class handler:
	def GET(self):
		if helper.logged(helper.PRIV_DELIVERY,'DELVERY_ORDER'):
			render = helper.create_render(globals={'str':str})
			param = web.input(status='')

			if param.status=='':
				return render.info('错误的参数！')

			# 查找门店
			db_shop = helper.get_shop_by_uid()

			condition={
				'shop'        : ObjectId(db_shop['shop']),
				'runner.uname' : helper.get_session_uname(),
			}
			if param.status=='DISPATCH':
				condition['status']='DISPATCH'
			elif param.status=='ONROAD':
				condition['status']='ONROAD'
			elif param.status=='COMPLETE':
				condition['status']='COMPLETE'
			else:
				condition['status']={'$nin':['COMPLETE','DISPATCH','ONROAD','DUE','TIMEOUT']}

			if param.status in ['COMPLETE']:
				tday = helper.time_str(format=1)
				begin_d = '%s 00:00:00' % tday
				end_d = '%s 23:59:59' % tday
				begin_t = int(time.mktime(time.strptime(begin_d,"%Y-%m-%d %H:%M:%S")))
				end_t = int(time.mktime(time.strptime(end_d,"%Y-%m-%d %H:%M:%S")))
				condition['$and']=[
					{'b_time' : {'$gt' : begin_t}},
					{'b_time' : {'$lt' : end_t}}
				]

			db_order=db.order_app.find(condition,
				{'order_id':1,'status':1,'address':1,'history':1}).sort([('_id',1)])
			return render.delivery_order(helper.get_session_uname(), helper.get_privilege_name(), 
				db_order, helper.ORDER_STATUS, param.status)
		else:
		    raise web.seeother('/')
