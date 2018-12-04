#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

# 退款统计

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	begin_date = '%s 00:00:00' % sys.argv[1]
	end_date = '%s 23:59:59' % sys.argv[2]

	condition = {
		'status' : {'$in':['CANCEL_TO_REFUND','FAIL_TO_REFUND']},  # 待退款订单
		'$and'   : [{'paid_time' : {'$gt' : begin_date}},
			    {'paid_time' : {'$lt' : end_date}}],
	}

	db_order = db.order_app.find(condition, {
		'order_id'     : 1,
		'status'       : 1,
		'sum_to_refund': 1,
		'paid_time'    : 1,
		'pay_type'     : 1,
		'type'         : 1,
		'due'          : 1,
		'uname'        : 1,
	}).sort([('paid_time',1)])

	print '日期,订单号,用户名,支付方式,实付金额,退款金额,订单状态'
	for u in db_order:
		print \
			u['paid_time'].encode('utf-8')+','+ \
			u['order_id'].encode('utf-8')+','+ \
			u['uname'].encode('utf-8')+','+ \
			u['pay_type'].encode('utf-8')+','+ \
			u['due'].encode('utf-8')+','+ \
			u.get('sum_to_refund',u['due']).encode('utf-8')+','+ \
			u['status'].encode('utf-8')

