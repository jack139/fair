#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys,datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

print '手机号,首单站点,9.9-9.15是否下单,下单数量,下单金额,9.16是否下单,下单数量,下单金额,9.17是否下单,下单数量,下单金额'

def user_detail(user):
	# print user
	if not user:
		return None

	db_order = db.order_app.find(
		{'uname': user, "status":"COMPLETE"}, 
		{"paid_time":1, "shop":1, "due":1}).sort("paid_time",1)
	if db_order.count() > 0:
		db_shop = db.base_shop.find_one({"_id":db_order[0]["shop"]}, {"name":1})
		print str(user)+",",
		print db_shop["name"].encode('utf-8')+",",
	else:
		print str(user)+",",
		print ''+",",

	# paid_time data >8.1, <8.31
	# 8.1-8.31的数据
	# 起至时间
	order_number = []
	paid_fee = []
	order_number2 = []
	paid_fee2 = []
	order_number3 = []
	paid_fee3 = []
	for i in db_order:
		condition = i["paid_time"] > u"2015-09-09 00:00:00" and i["paid_time"] < u"2015-09-15 23:59:59" 
		if condition:
			order_number.append(i["paid_time"])
			paid_fee.append(float(i["due"]))

		condition = i["paid_time"] > u"2015-09-16 00:00:00" and i["paid_time"] < u"2015-09-16 23:59:59" 
		if condition:
			order_number2.append(i["paid_time"])
			paid_fee2.append(float(i["due"]))

		condition = i["paid_time"] > u"2015-09-17 00:00:00" and i["paid_time"] < u"2015-09-17 23:59:59" 
		if condition:
			order_number3.append(i["paid_time"])
			paid_fee3.append(float(i["due"]))

	if len(order_number) > 0:
		print "是"+",",
	else:
		print "否"+",",
	print str(len(order_number))+",",
	print str(sum(paid_fee))+",",

	if len(order_number2) > 0:
		print "是"+",",
	else:
		print "否"+",",
	print str(len(order_number2))+",",
	print str(sum(paid_fee2))+",",

	if len(order_number3) > 0:
		print "是"+",",
	else:
		print "否"+",",
	print str(len(order_number3))+",",
	print str(sum(paid_fee3))

	# 初始化data

if __name__ == "__main__":
	# 读取号码
	f = open("20150916.num.txt", "rt")

	user2 = [j.strip('\r\n') for j in f.readlines()]

	# print user2
	for u in user2:
		# print u
		# print j.strip('\r\n')
		user_detail(u)
	# user_detail("18516569412")


