#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('ipcam','zjjL_3026')

ISOTIMEFORMAT=['%Y-%m-%d %X', '%Y-%m-%d', '%Y%m%d%H%M']

def time_str(t=None, format=0):
    return time.strftime(ISOTIMEFORMAT[format], time.localtime(t))


# 退款统计

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date> -list" % sys.argv[0]
		sys.exit(2)

	begin_date = '%s 00:00:00' % sys.argv[1]
	end_date = '%s 23:59:59' % sys.argv[2]

	if len(sys.argv)>3 and sys.argv[3]=='-list':
		just_list = True
	else:
		just_list = False

	condition = {
		'type'   : {'$in':['TUAN','SINGLE']},
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
		'wx_out_trade_no':1,
	}).sort([('paid_time',1)])

	#print '订单号 金额 说明'
	for u in db_order:
		if u['pay_type']!='WXPAY':
			continue

		if just_list==False: 
			# 修改订单状态
			db.order_app.update_one({'_id':u['_id']},{
				'$set'  : {'status'  : 'REFUND'},
				'$push' : {'history' : (time_str(), 'script', '退款完成')}
			})

		if len(u.get('wx_out_trade_no',''))>0:
			order_id = u['wx_out_trade_no'].encode('utf-8')
		else:
			order_id = u['order_id'].encode('utf-8')
		print \
			order_id+' '+ \
			'%.2f'%float(u.get('sum_to_refund',u['due']))+' '+ \
			'系统退款'

