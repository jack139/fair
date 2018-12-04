#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

# 统计报损

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	shops={}
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}},{'name':1})
	for i in db_shop:
		shops[i['_id']]=i['name']

	begin_date = '%s 00:00:00' % sys.argv[1]
	end_date = '%s 23:59:59' % sys.argv[2]

	condition = {
		'$and'   : [{'history.0.0' : {'$gt' : begin_date}},
			    {'history.0.0' : {'$lt' : end_date}}],
	}

	db_order = db.order_damage.find(condition)

	print '日期,门店,商品代码,报损数量,操作用户'
	for u in db_order:
		print \
			u['history'][0][0].encode('utf-8')+','+ \
			shops[u['shop']].encode('utf-8')+','+ \
			u['product_id'].encode('utf-8')+','+ \
			u['num'].encode('utf-8')+','+ \
			u['history'][0][1].encode('utf-8')

