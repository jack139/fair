#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')


if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	# 起至时间
	begin_d = sys.argv[1]
	end_d = sys.argv[2]

	begin_date = '%s 00:00:00' % begin_d
	end_date = '%s 23:59:59' % end_d


	condition = {
		'status' : 'PAID',
		'$and'   : [{'paid_time' : {'$gt' : begin_date}},
			    {'paid_time' : {'$lt' : end_date}}],
	}


	# 统计线下订单
	db_sale = db.order_offline.find(condition, 
		{'order_id':1,'due':1,'pay':1,'change':1,'paid_time':1,'cart':1})

	skus = {}
	#total = 0.0
	#count = 0
	for i in db_sale:
		#ttt = 0.0
		for j in i['cart']:
			#ttt += float(j['price'])
			if skus.has_key(j['product_id']):
				#skus[j['product_id']]['offline']['cost'] += float(j['cost'])
				skus[j['product_id']]['offline']['price'] += float(j['price'])
				skus[j['product_id']]['offline']['num'] += float(j['num'])
			else:
				skus[j['product_id']]={
					'offline' : {
						#'cost'  : float(j['cost']),
						'price' : float(j['price']),
						'num'   : float(j['num']),
					},
					'online' : {
						#'cost'  : 0.0,
						'price' : 0.0,
						'num'   : 0.0,
					},							
					'name'  : j['name'],
				}
		#print i['due'], ttt
		#total += float(i['due'])
		#count += 1

	# 统计线上订单
	condition['status']={'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']}
	condition['type'] =  {'$nin':['TUAN','SINGLE']} # 过滤拼团
	db_sale2 = db.order_app.find(condition, 
		{'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1,'shop':1})

	#total3_dark = 0.0
	#total4_dark = 0.0
	#count3_dark = 0
	#total3 = 0.0
	#total4 = 0.0
	#count3 = 0
	for i in db_sale2:
		for j in i['cart']:
			if skus.has_key(j['product_id']):
				#skus[j['product_id']]['online']['cost'] += float(j['cost'])
				skus[j['product_id']]['online']['price'] += float(j['price'])
				skus[j['product_id']]['online']['num'] += float(j['num2'])
			else:
				skus[j['product_id']]={
					'online' : {
						#'cost'  : float(j['cost']),
						'price' : float(j['price']),
						'num'   : float(j['num2']),
					},
					'offline' : {
						#'cost'  : 0.0,
						'price' : 0.0,
						'num'   : 0.0,
					},							
					'name'  : j['title'],
				}
		#if shop_type[i['shop']]=='dark': # 暗店
		#	total3_dark += float(i['due'])
		#	total4_dark += float(i['total'])
		#	count3_dark += 1
		#else:	# 明店
		#	total3 += float(i['due'])
		#	total4 += float(i['total'])
		#	count3 += 1

	'''
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
	'''
	#print total, total2

	# 返回csv格式文本
	print '开始日期,结束日期,商品代码,商品名称,线上数量,线上金额,线下数量,线下金额'
	for i in skus.keys():
		#print i, skus[i]
		print \
			begin_d + ',' + \
			end_d + ',' + \
			i.encode('utf-8') + ',' + \
			skus[i]['name'].encode('utf-8') + ',' + \
			('%.2f' % skus[i]['online']['num']) + ',' + \
			('%.2f' % skus[i]['online']['price']) + ',' + \
			('%.2f' % skus[i]['offline']['num']) + ',' + \
			('%.2f' % skus[i]['offline']['price'])

