#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/report')

# - 销货记录 －－－－－－－－－－－
class handler:        #class PosReport:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_REPORT'):
			render = helper.create_render()
			user_data=web.input(start_date='')
			
			if user_data['start_date']=='':
				return render.pos_report(helper.get_session_uname(), helper.get_privilege_name())

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 起至时间
			begin_date = '%s 00:00:00' % user_data['start_date']
			end_date = '%s 23:59:59' % user_data['start_date']

			#print begin_date, end_date, db_shop['_id']

			# 统计线下订单
			db_sale = db.order_offline.find({
				'shop'   : db_shop['shop'],
				'status' : 'PAID',
				'$and'   : [{'paid_time' : {'$gt' : begin_date}},
					    {'paid_time' : {'$lt' : end_date}}],
			}, {'order_id':1,'due':1,'pay':1,'change':1,'paid_time':1,'cart':1})

			skus = {}
			total = 0.0
			count = 0
			for i in db_sale:
				#ttt = 0.0
				for j in i['cart']:
					#ttt += float(j['price'])
					if skus.has_key(j['product_id']):
						skus[j['product_id']]['offline']['cost'] += float(j['cost'])
						skus[j['product_id']]['offline']['price'] += float(j['price'])
						skus[j['product_id']]['offline']['num'] += float(j['num'])
					else:
						skus[j['product_id']]={
							'offline' : {
								'cost'  : float(j['cost']),
								'price' : float(j['price']),
								'num'   : float(j['num']),
							},
							'online' : {
								'cost'  : 0.0,
								'price' : 0.0,
								'num'   : 0.0,
							},							
							'name' : j['name'],
						}
				#print i['due'], ttt
				total += float(i['due'])
				count += 1

			# 统计线上订单
			db_sale2 = db.order_app.find({
				'shop'   : db_shop['shop'],
				'status' : 'COMPLETE', # 只统计已完成的订单
				'$and'   : [{'paid_time' : {'$gt' : begin_date}},
					    {'paid_time' : {'$lt' : end_date}}],
			}, {'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1})

			total3 = 0.0
			total4 = 0.0
			count3 = 0
			for i in db_sale2:
				for j in i['cart']:
					if skus.has_key(j['product_id']):
						skus[j['product_id']]['online']['cost'] += float(j['cost'])
						skus[j['product_id']]['online']['price'] += float(j['price'])
						skus[j['product_id']]['online']['num'] += float(j['num2'])
					else:
						skus[j['product_id']]={
							'online' : {
								'cost'  : float(j.get('cost','0.00')),
								'price' : float(j['price']),
								'num'   : float(j['num2']),
							},
							'offline' : {
								'cost'  : 0.0,
								'price' : 0.0,
								'num'   : 0.0,
							},							
							'name'  : j['title'],
						}
				total3 += float(i['due'])
				total4 += float(i['total'])
				count3 += 1


			# 统计退货
			db_return = db.order_return.find({
				'shop' : db_shop['shop'],
				'$and' : [{'return_time' : {'$gt' : begin_date}},
					  {'return_time' : {'$lt' : end_date}}],
			}, {'product_id':1, 'total':1,'return_time':1})

			# 退货单流水
			total2 = 0.0
			count2 = 0
			for i in db_return:
				count2 += 1
				total2 += float(i['total'])

			#print total, total2

			return render.pos_report_result2(helper.get_session_uname(), helper.get_privilege_name(), 
				skus, len(skus), 
				('%.2f' % total4, '%.2f' % (total4-total3), '%.2f' % total3), # 线上
				('%.2f' % total, '%.2f' % total2, '%.2f' % (total-total2)), # 线下
				(count3, count, count2),
				user_data.start_date)


		else:
			raise web.seeother('/')


