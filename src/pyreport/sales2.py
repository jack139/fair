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

	shops={}
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}},{'name':1})
	for i in db_shop:
		shops[i['_id']]=i['name']

	# 起至时间
	begin_d = sys.argv[1]
	end_d = sys.argv[2]

	begin_date = '%s 00:00:00' % begin_d
	end_date = '%s 23:59:59' % end_d
			
	#print begin_date, end_date, db_shop['_id']

	condition = {
		'type'   : {'$nin':['TUAN','SINGLE']}, # 过滤拼团
		'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']},
		'$and'   : [{'paid_time' : {'$gt' : begin_date}},
			    {'paid_time' : {'$lt' : end_date}}],
	}

	# 统计线上订单
	db_sale = db.order_app.find(condition, 
		{'order_id':1,'shop':1,'paid_time':1,'uname':1,'due':1,'address':1,'first_disc':1,'cart':1})

	#print db_sale.count()
	
	orders=[]
	for i in db_sale:
		if float(i['first_disc'])>0:
			new_user = u'是'
		else:
			new_user = u''
		orders.append((
			shops[i['shop']], # 0
			i['order_id'], # 1
			i['paid_time'], # 2
			u'微信' if len(i['uname'])>15 else i['uname'], # 3
			i['due'], # 4
			i['address'][1], # 5
			i['address'][2], # 6
			i['address'][3], # 7
			new_user, # 8
			u';'.join(u'%s %s 金额 %s 数量 %s' % \
				(x['product_id'],x['title'],x['price'],x['num']) for x in i['cart']), #9
		))

	# 返回csv格式文本
	print '站点名称,订单编号,付款时间,下单手机号,付款金额,收货姓名,收货电话,收货地址,是否新客,购物车'
	for i in orders:
		print (','.join(i)).encode('utf-8')
