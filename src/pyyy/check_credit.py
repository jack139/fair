#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import os, time, sys
from pymongo import MongoClient

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')


if __name__ == "__main__":
	if len(sys.argv)<2:
		print "usage: python %s <mobile>" % sys.argv[0]
		sys.exit(2)

	uname = sys.argv[1]

	r = db.app_user.find_one({'uname':uname},{'credit_history':1,'credit':1})
	if r:
		print '余额：%.2f' % r.get('credit', 0)
		for i in r.get('credit_history', []):
			print i[0],i[1],i[2],i[3]
	else:
		print '未知号码'

