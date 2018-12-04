#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys,datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

db2 = MongoClient('10.168.11.151')['report_db']
db2.authenticate('owner','owner')


# 按店按商品，14点前销量和全天销量

if __name__ == "__main__":
	if len(sys.argv)<2:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	shops={}
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}},{'name':1})
	for i in db_shop:
		shops[i['_id']]=i['name']

	# 起至时间
	begin_d = sys.argv[1]
	end_d = sys.argv[2]

	#begin_date = '%s 00:00:00' % begin_d
	#end_date = '%s 23:59:59' % end_d

	# 生成每天时间
	d1 = begin_d.split('-')
	d2 = end_d.split('-')
	dt = datetime.date(int(d1[0]),int(d1[1]),int(d1[2]))
	end = datetime.date(int(d2[0]),int(d2[1]),int(d2[2]))
	step = datetime.timedelta(days=1)

	days = []
	while dt <= end:
		days.append(dt.strftime('%Y-%m-%d'))
		dt += step

	#print days

	# 查询当前的库存信息，并输出
	print '日期,门店,商品代码,商品名,14点销量,全天销量'

	# 只计算昨天和今天的销量
	for day in days:
		begin_date = '%s 00:00:00' % day
		end_date = '%s 23:59:59' % day
		check_date = '%s 14:00:00' % day

		condition = {
			'type'   : {'$nin':['TUAN','SINGLE']},
			'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']},
			'$and'   : [{'paid_time' : {'$gt' : begin_date}},
				    {'paid_time' : {'$lt' : end_date}}],
		}

		db_sale2 = db.order_app.find(condition, 
			{'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1,'shop':1}).sort([("paid_time",1)])

		skus = {}
		for i in db_sale2:
			for j in i['cart']:
				if skus.has_key((i['shop'],j['product_id'])):
					if i['paid_time'] <= check_date:
						skus[(i['shop'],j['product_id'])]['online']['num'] += float(j['num2'])
						skus[(i['shop'],j['product_id'])]['online']['num_all'] += float(j['num2'])
					else:
						skus[(i['shop'],j['product_id'])]['online']['num_all'] += float(j['num2'])
				else:
					if i['paid_time'] <= check_date:
						num = num_all = float(j['num2'])
					else:
						num_all = float(j['num2'])
						num = 0

					skus[(i['shop'],j['product_id'])]={
						'online' : {
							'num'     : num,
							'num_all' : num_all,
						},
						'name'  : j['title'],
					}

		# 按店拉数据
		for shop in shops.keys():
			db_invent = db.inventory.find({'shop':shop},{'product_id':1,'price':1,'num':1})

			for i in db_invent:
				if i['product_id'][0]=='w' or i['product_id'][2]=='2': #忽略称重项目
					continue

				if not skus.has_key((shop, i['product_id'])):
					continue

				data_item = {
					'shop_name' : shops[shop],
					'product_id' : i['product_id'],
					'title' : skus[(shop, i['product_id'])]['name'],
					'num' : skus[(shop, i['product_id'])]['online']['num'],
					'num_all' : skus[(shop, i['product_id'])]['online']['num_all'] 
				}

				print \
					day+','+ \
					data_item['shop_name'].encode('utf-8')+','+ \
					data_item['product_id'].encode('utf-8')+','+ \
					data_item['title'].encode('utf-8')+','+ \
					'%d' % data_item['num']+','+ \
					'%d' % data_item['num_all']

