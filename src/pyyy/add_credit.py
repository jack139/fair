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
    return time.strftime('%Y-%m-%d %X', time.localtime(t))

# 来自文件
# 格式：
# 号码,金额
#
f=open('./phone_credit.txt')
a=f.readlines()
f.close()

user_list = a

if __name__ == "__main__":
	for u0 in user_list:
		# 忽略空行
		if len(u0.strip())==0:
			continue
		# 忽略井号开头
		if u0.strip()[0]=='#':
			continue

		u1 = u0.strip().split(',')

		# 忽略只有号码, 没金额的
		if len(u1)<2:
			continue

		u = u1[0].strip()
		try:
			money = float(u1[1])
		except ValueError: # 金额格式有问题，忽略
			print 'fail: ', u0
			money = 0
			continue

		if len(u)>11:
			condition = {'openid':u }
		else:
			condition = {'uname':u }

		# 充值
		db.app_user.update_one(condition,{
			'$inc'  : { 'credit': money },
			'$push' : { 'credit_history' : ( time_str(), '系统充值', '＋%.2f' % money, '')}
		})

		# 日志
		db2.script_log.insert_one({
			'type'   : 'add_credit',
			'time'   : time.ctime(),
			'uname'  : u,
			'money'  : money
		})
		print u0

