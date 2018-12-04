#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os, time, sys, gc, random
from pymongo import MongoClient
from bson.objectid import ObjectId
from coupon_setting import *

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('ipcam','zjjL_3026')

db2 = MongoClient('10.168.11.151')['report_db']
db2.authenticate('owner','owner')


def time_str(t=None):
    return time.strftime('%Y-%m-%d', time.localtime(t))

def my_rand(n=4):
	import random
	return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for ch in range(n)])

# 来自文件
f=open('./phone_num.txt')
a=f.readlines()
f.close()

user_list = a

if __name__ == "__main__":
	valid = time_str(time.time()+3600*24*expire_days)
	for u0 in user_list:
		# 忽略空行
		if len(u0.strip())==0:
			continue
		# 忽略井号开头
		if u0.strip()[0]=='#':
			continue

		u = u0.strip()
		if len(u)>11:
			condition = {'openid':u }
		else:
			condition = {'uname':u }

		# 添加所有优惠券
		for i in new_coupon:
			# 生成优惠券
			new_one = (my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2])

			# 添加
			db.app_user.update_one(condition, { '$push' : { 'coupon' : new_one }})

			# 记录日志
			db2.script_log.insert_one({
				'type'   : 'add_coupon',
				'time'   : time.ctime(),
				'uname'  : u,
				'coupon' : new_one
			})
			print u, new_one

