#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os, time, sys, gc, random
from pymongo import MongoClient
from bson.objectid import ObjectId
from coupon_setting import *

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('ipcam','zjjL_3026')

# 来自测试
#code_list = [
#	'zj01'
#]


# 来自文件
f=open('./invite_code.txt')
a=f.readlines()
f.close()

code_list = a

if __name__ == "__main__":
	for i in code_list:
		code = i.strip().lower()
		if len(code)==0: # 忽略长度为零
			continue
		if code[0]=='#': # 忽略注释
			#print code
			continue
		db.invitation.update_one({'code':code}, {'$set':{'code':code}}, upsert=True)
   		print code
