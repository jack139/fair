#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')


# 统计订单重复购买

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	begin_date = '%s 00:00:00' % sys.argv[1]
	end_date = '%s 23:59:59' % sys.argv[2]

	condition = {
		'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL']},
		'$and'   : [{'paid_time' : {'$gt' : begin_date}},
			    {'paid_time' : {'$lt' : end_date}}],
	}

	db_order = db.order_app.find(condition, 
		{'order_id':1,'shop':1,'paid_time':1,'uname':1,'due':1,'address':1,'first_disc':1}
	)

	result = {}
	for u in db_order:
		if result.has_key(u['uname']):
			result[u['uname']]['num'] += 1
			result[u['uname']]['due'] += float(u['due'])
		else:
			result[u['uname']] = {'num' : 1, 'due':float(u['due'])}

	print '开始日期,结束日期,用户ID,'
	for i in result.keys():
		print \
			sys.argv[1]+','+ \
			sys.argv[2]+','+ \
			i.encode('utf-8')+','+ \
			('%d' % result[i]['num'])+','+ \
			('%.2f' % result[i]['due'])

