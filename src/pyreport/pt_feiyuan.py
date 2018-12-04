#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

ISOTIMEFORMAT=['%Y-%m-%d %X', '%Y-%m-%d', '%Y%m%d%H%M']

def time_str(t=None, format=0):
    return time.strftime(ISOTIMEFORMAT[format], time.localtime(t))

# 飞远面单数据

if __name__ == "__main__":
	if len(sys.argv)<2:
		print "usage: python %s <region_id>" % sys.argv[0]
		print "001 - 东南"
		print "002 - 华北"
		print "003 - 华东"
		sys.exit(2)

	region_id = sys.argv[1]

	condition = {
		'status' : 'DISPATCH',  # 待派送订单
		'type'   : {'$in':['TUAN','SINGLE']},
		'region_id' : region_id,
	}

	db_order = db.order_app.find(condition, {
		'order_id'     : 1,
		'status'       : 1,
		'cart'         : 1,
		'address'      : 1,
		'due'          : 1,
		'type'         : 1,
		'uname'        : 1,
		'crm_text'     : 1,
	}).sort([('paid_time',1)])

	print '活动编号,订单类型,业务名,Email日期,订单号,出库单号,发货单号,商品明细,重量,地址,姓名,电话,手机,应收款,体积,包裹数,客服备注'
	for u in db_order:
		print \
			u['cart'][0]['tuan_id'].encode('utf-8')+','+ \
			'0'+','+ \
			'浙江优展'+','+ \
			time_str(format=1)+','+ \
			u['order_id'].encode('utf-8')+','+ \
			'0'+','+ \
			'0'+','+ \
			u['cart'][0]['title'].encode('utf-8')+','+ \
			'0'+','+ \
			''.join(u['address'][8].split(',')).encode('utf-8')+u['address'][3].encode('utf-8')+','+ \
			u['address'][1].encode('utf-8')+','+ \
			u['address'][2].encode('utf-8')+','+ \
			u['address'][2].encode('utf-8')+','+ \
			'0'+','+ \
			'0'+','+ \
			'1'+','+ \
			(''.join(x if x[:3]!='201' else '' for x in u.get('crm_text',u'').encode('utf-8').split('\r\n'))).replace(',','.').replace(' ','')

