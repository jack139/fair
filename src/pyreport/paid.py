#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

status_name = { # 线上订单
	'name'     : '线上订单',
	'DUE'      : '待支付',
	'PREPAID'  : '付款确认中',
	'PAID'     : '已付款',
	'DISPATCH' : '已拣货，待配送',
	'ONROAD'   : '配送中',
	'COMPLETE' : '配送完成',
	'FINISH'   : '已完成',
	'CANCEL'   : '已取消',
	'TIMEOUT'  : '已过付款期限',
	'GAP'      : '缺货处理',
	'REFUND'   : '已退款',
	'FAIL'     : '配送失败',
	'CANCEL1'  : '第3方取消订单1',
	'CANCEL2'  : '第3方取消订单2',
	'CANCEL3'  : '第3方取消订单3',
	'CANCEL4'  : '第3方取消订单4',
	# 拼团使用
	'PAID_AND_WAIT'    : '等待成团',
	'FAIL_TO_REFUND'   : '拼团失败',
	'CANCEL_TO_REFUND' : '拼团取消'
}
# 暗店统计支付订单

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
		'status' : {'$nin':['TIMEOUT','DUE','CANCEL']},  # 包含REFUND订单
		'$and'   : [{'paid_time' : {'$gt' : begin_date}},
			    {'paid_time' : {'$lt' : end_date}}],
	}

	db_order = db.order_app.find(condition, {
		'order_id'     : 1,
		'status'       : 1,
		'shop'         : 1,
		'paid_time'    : 1,
		'ali_trade_no' : 1,
		'wx_trade_no'  : 1,
		'total'        : 1,
		'delivery_fee' : 1,
		'first_disc'   : 1,
		'coupon_disc'  : 1,
		'due'          : 1,
		'uname'        : 1,
		'pay_type'     : 1,
	}).sort([('paid_time',1)])

	print '日期,门店,订单号,用户名,商品金额,运费,合计应收,首单立减,优惠券,实付金额,支付方式,订单状态,'
	for u in db_order:
		if u.has_key('pay_type'):
			if u['pay_type']=='WXPAY':
				if len(u['uname'])>11:
					pay_type='公众号微信支付'
				else:
					pay_type='APP微信支付'
			elif u['pay_type']=='ALIPAY':
				pay_type='支付宝支付'
			elif u['pay_type']=='CREDIT':
				pay_type='余额支付'
			elif u['pay_type']=='elm':
				pay_type='饿了吗'
			else:
				pay_type='未知'
		else:
			if len(u['uname'])>11:
				pay_type='公众号微信支付'
			else:
				if u.has_key('wx_trade_no'):
					pay_type='APP微信支付'
				elif u.has_key('ali_trade_no'):
					pay_type='支付宝支付'
				else:
					pay_type='余额支付'

		print \
			u['paid_time'].encode('utf-8')+','+ \
			shops[u['shop']].encode('utf-8')+','+ \
			u['order_id'].encode('utf-8')+','+ \
			u['uname'].encode('utf-8')+','+ \
			u['total'].encode('utf-8')+','+ \
			u['delivery_fee'].encode('utf-8')+','+ \
			('%.2f' % (float(u['delivery_fee'])+float(u['total'])))+','+ \
			str(u['first_disc']).encode('utf-8')+','+ \
			str(u['coupon_disc']).encode('utf-8')+','+ \
			u['due'].encode('utf-8')+','+ \
			pay_type+','+ \
			status_name[u['status'].encode('utf-8')]

