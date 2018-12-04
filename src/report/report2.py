#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/report/report2')

# - 销货记录 所有门店－－－－－－－－－－－
class handler:        #class PosReport:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'REPORT_REPORT2'):
			render = helper.create_render()
			user_data=web.input(start_date='', shop='__ALL__')
			
			if user_data['start_date']=='':
				db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark','counter']}},{'name':1})
				return render.report_report2(helper.get_session_uname(), helper.get_privilege_name(), db_shop)

			# 查找shop
			#db_shop = helper.get_shop_by_uid()

			# 起至时间
			begin_date = '%s 00:00:00' % user_data['start_date']
			end_date = '%s 23:59:59' % user_data['start_date']

			condition = {
				#'shop'   : db_shop['shop'],
				'status' : 'PAID',
				#'type'   : {'$nin': ['TUAN', 'SINGLE']},
				'$and'   : [{'paid_time' : {'$gt' : begin_date}},
					    {'paid_time' : {'$lt' : end_date}}],
			}

			if user_data['shop']!='__ALL__':
				condition['shop'] = ObjectId(user_data['shop'])
				db_shop = helper.get_shop(condition['shop'])
				shop_name = db_shop['name']
			else:
				shop_name = '全部门店'

			shop_type={}
			db_shop_type = db.base_shop.find({},{'type':1})
			for s in db_shop_type:
				shop_type[s['_id']]=s['type']

			# 统计线下订单
			db_sale = db.order_offline.find(condition, 
				{'order_id':1,'due':1,'pay':1,'change':1,'paid_time':1,'cart':1,'type':1})

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
								'cost'  : float(j.get('cost','0.00')),
								'price' : float(j['price']),
								'num'   : float(j['num']),
							},
							'online' : {
								'cost'  : 0.0,
								'price' : 0.0,
								'num'   : 0.0,
								'paid'  : 0.0,
							},							
							'name'  : j['name'],
						}
				#print i['due'], ttt
				total += float(i['due'])
				count += 1

			# 统计线上订单
			condition['status']={'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND','CANCEL1','CANCEL2','CANCEL3','CANCEL4','FAIL_TO_REFUND','CANCEL_TO_REFUND','PAID_AND_WAIT']}
			db_sale2 = db.order_app.find(condition, 
				{'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1,'shop':1,'type':1,'status':1,'delivery_fee':1})

			total3_dark = 0.0
			total4_dark = 0.0
			count3_dark = 0
			total3 = 0.0
			total4 = 0.0
			count3 = 0
			for i in db_sale2:

				if i.get('type') in ['TUAN','SINGLE']: # 拼团订单
					if skus.has_key(i['cart'][0]['tuan_id']):
						skus[i['cart'][0]['tuan_id']]['online']['cost'] = 0.0
						skus[i['cart'][0]['tuan_id']]['online']['price'] += float(i['due'])
						skus[i['cart'][0]['tuan_id']]['online']['num'] += 1
						skus[i['cart'][0]['tuan_id']]['online']['paid'] += (1 if i['status']=='PAID' else 0)
						skus[i['cart'][0]['tuan_id']]['online']['dispatch'] += (1 if i['status']=='DISPATCH' else 0)
						skus[i['cart'][0]['tuan_id']]['online']['onroad'] += (1 if i['status']=='ONROAD' else 0)
					else:
						skus[i['cart'][0]['tuan_id']]={
							'online' : {
								'cost'  : 0.0,
								'price' : float(i['due']),
								'num'   : 1, # 要包含送的
								'paid'  : 1 if i['status']=='PAID' else 0, # 已付款，待拣货的， 拼团用
								'dispatch'  : 1 if i['status']=='DISPATCH' else 0, # 已付款，待配送， 拼团用
								'onroad'  : 1 if i['status']=='ONROAD' else 0, # 已付款，配送中， 拼团用
							},
							'offline' : {
								'cost'  : 0.0,
								'price' : 0.0,
								'num'   : 0.0,
							},							
							'name'  : i['cart'][0].get('title','n/a'),
						}
				else: # 普通订单
					for j in i['cart']:
						if skus.has_key(j['product_id']):
							skus[j['product_id']]['online']['cost'] += float(j.get('cost','0.00'))
							skus[j['product_id']]['online']['price'] += float(j['price'])
							# 要包含送的
							skus[j['product_id']]['online']['num'] += (float(j['num2'])+float(j.get('numyy','0.00')))
						else:
							skus[j['product_id']]={
								'online' : {
									'cost'  : float(j.get('cost','0.00')),
									'price' : float(j['price']),
									'num'   : float(j['num2'])+float(j.get('numyy','0.00')), # 要包含送的
									'paid'  : 0, # 普通订单不用这字段
									'dispatch'  : 0, # 普通订单不用这字段
									'onroad'  : 0, # 普通订单不用这字段
								},
								'offline' : {
									'cost'  : 0.0,
									'price' : 0.0,
									'num'   : 0.0,
								},							
								'name'  : j['title'],
							}
				if shop_type[i['shop']]=='dark': # 暗店
					total3_dark += float(i['due'])
					total4_dark += (float(i['total'])+float(i['delivery_fee']))
					count3_dark += 1

				else:	# 明店
					total3 += float(i['due'])
					total4 += float(i['total'])
					count3 += 1


			# 统计退货
			condition2 = {
				#'shop' : db_shop['shop'],
				'$and' : [{'return_time' : {'$gt' : begin_date}},
					  {'return_time' : {'$lt' : end_date}}],
			}
			if condition.has_key('shop'):
				condition2['shop'] = condition['shop']
			db_return = db.order_return.find(condition2, {'product_id':1, 'total':1,'return_time':1})

			# 退货单流水
			total2 = 0.0
			count2 = 0
			for i in db_return:
				count2 += 1
				total2 += float(i['total'])

			#print 'test', total3_dark, total4_dark

			return render.report_report2_r(helper.get_session_uname(), helper.get_privilege_name(), 
				skus, len(skus), 
				('%.2f' % total4_dark, '%.2f' % (total4_dark-total3_dark), '%.2f' % total3_dark, # 线上暗店
				'%.2f' % total4, '%.2f' % (total4-total3), '%.2f' % total3), # 线上明店
				('%.2f' % total, '%.2f' % total2, '%.2f' % (total-total2)), # 线下
				(count3, count, count2, count3_dark),
				user_data.start_date, shop_name,
				user_data['shop'] in setting.PT_shop.values())

		else:
			raise web.seeother('/')


