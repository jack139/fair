#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/report_user')

# - 当前用户的销货记录 －－－－－－－－－－－
class handler:        #class PosReport:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_REPORT_USER'):
			render = helper.create_render(globals={'round':round})
			user_data=web.input(start_date='')
			
			if user_data['start_date']=='':
				return render.pos_report_user(helper.get_session_uname(), helper.get_privilege_name())

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			begin_date = '%s 00:00:00' % user_data['start_date']
			end_date = '%s 23:59:59' % user_data['start_date']

			#print begin_date, end_date, db_shop['_id']

			# 统计销货
			db_sale = db.order_offline.find({
				'shop' : db_shop['shop'],
				'user' : helper.get_session_uname(),
				'status' : 'PAID',
				'$and' : [{'paid_time' : {'$gt' : begin_date}},
					  {'paid_time' : {'$lt' : end_date}}],
			}, {'order_id':1,'due':1,'pay':1,'change':1,'paid_time':1})

			# 销货单流水
			total = 0.0
			count = 0
			for i in db_sale:
				count += 1
				total += float(i['due'])

			# 统计退货
			db_return = db.order_return.find({
				'shop' : db_shop['shop'],
				'user' : helper.get_session_uname(),
				'$and' : [{'return_time' : {'$gt' : begin_date}},
					  {'return_time' : {'$lt' : end_date}}],
			}, {'total':1,'return_time':1})

			# 退货单流水
			total2 = 0.0
			count2 = 0
			for i in db_return:
				count2 += 1
				total2 += float(i['total'])

			return render.pos_report_user_ret(helper.get_session_uname(), helper.get_privilege_name(),
				count, total, count2, total2, user_data.start_date)

		else:
			raise web.seeother('/')


