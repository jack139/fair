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

# 飞远面单派送结果

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <command> <file-name>" % sys.argv[0]
		print "m - change to COMPLETE, use feiyuan output format"
		print "r - change to ONROAD, use feiyuan input format"
		sys.exit(2)

	command = sys.argv[1]
	file_name = sys.argv[2]

	if command not in ['m', 'r']:
		print "Unknown command."
		sys.exit(2)

	# 来自文件
	f=open(file_name)
	code_list=f.readlines()
	f.close()

	for i in code_list:
		code = i.strip().lower().split(',')
		if len(code)<11:
			continue

		if command=='m': # 刷complete
			order_id = code[2] # 格式变动需要调整
			status0 = code[10] # 格式变动需要调整
 
			if status0!='成功':
			#	print '! ', order_id, status
				continue
			else:
				last_status = 'ONROAD'
				status = 'COMPLETE'

		elif command=='r': # 刷onroad
			order_id = code[4] # 格式变动需要调整
			last_status = 'DISPATCH'
			status = 'ONROAD'		

		print order_id

		# 更新订单状态
		r = db.order_app.find_one_and_update({
				'order_id' : order_id,
				'status'   : last_status,
			}, 
			{
				'$set' : {
					'status'  : status,
					'man'     : 0,
				},
				'$push' : {'history' : (time_str(), 'script', '状态转换为'+status)}
			},
			{'_id':1, 'status':1, 'uname':1}
		)
		if r==None:
			r2 = db.order_app.find_one({'order_id' : order_id},{'status':1})
			print 'not found: ', order_id, r2['status']

	print 'Done.'

