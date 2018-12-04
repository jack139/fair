#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys,datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

# 按天按店统计销售

def check_app_type(uname):
	db_user=db.app_user.find_one({'uname':uname},{'app_id':1})
	if db_user==None:
		return None
	db_device=db.app_device.find_one({'app_id':db_user['app_id']},{'type':1})
	if db_device==None:
		#print 'cannot find device', db_user['app_id']
		app_type='ANDROID'
	else:
		app_type=db_device['type']
	return app_type

if __name__ == "__main__":
	if len(sys.argv)<3:
		print "usage: python %s <begin_date> <end_date>" % sys.argv[0]
		sys.exit(2)

	shops={}
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}},{'name':1})
	for i in db_shop:
		shops[i['_id']]=i['name']

	# 起至时间
	begin_d = sys.argv[1]
	end_d = sys.argv[2]

	# 生成每天时间
	d1 = begin_d.split('-')
	d2 = end_d.split('-')
	dt = datetime.date(int(d1[0]),int(d1[1]),int(d1[2]))
	end = datetime.date(int(d2[0]),int(d2[1]),int(d2[2]))
	step = datetime.timedelta(days=1)

	days = []
	while dt <= end:
		days.append(dt.strftime('%Y-%m-%d'))
		dt += step

	#print days

	print '日期,终端,门店,订单数,总交易额,客单价,顾客数,新客数,老客数'

	for day in days:
		begin_date = '%s 00:00:00' % day
		end_date = '%s 23:59:59' % day

		#print begin_date, end_date, begin_date_last, end_date_last

		data={}
		user_this={}
		for i in shops.keys():
			# 初始化data表格
			data[i]={ # order_num #0, due_sum #1, new_user #2, old_user #3, lastweek #4, thisweek #5
				'H5'      : [0,0.0,[],[],0,0],
				'IOS'     : [0,0.0,[],[],0,0],
				'ANDROID' : [0,0.0,[],[],0,0],
			}

			# 统计这个周期订单
			condition = {
				'shop'   : ObjectId(i),
				'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']},
				'$and'   : [{'paid_time' : {'$gt' : begin_date}},
					    {'paid_time' : {'$lt' : end_date}}],
			}

			# 统计这个周期订单
			db_sale = db.order_app.find(condition, 
				{'order_id':1,'shop':1,'paid_time':1,'uname':1,'due':1,'first_disc':1})

			for j in db_sale:
				if len(j['uname'])>11: # 微信
					app_type='H5'
				elif user_this.has_key(j['uname']): # 已有记录
					app_type=user_this[j['uname']]
				else: # app，确定app类型
					app_type=check_app_type(j['uname'])
					if app_type==None:
						print 'cannot find user', j['uname'], j['order_id']
						continue
				# 记录用户名
				user_this[j['uname']]=app_type

				data[i][app_type][0] += 1
				data[i][app_type][1] += float(j['due'])
				if float(j['first_disc'])>0:
					if j['uname'] not in data[i][app_type][2]:
						(data[i][app_type][2]).append(j['uname'])
				else:
					if j['uname'] not in data[i][app_type][3]:
						(data[i][app_type][3]).append(j['uname'])


		for i in data.keys():
			for j in data[i].keys():
				print \
					(day+','+ \
					j+','+ \
					shops[i]+','+ \
					'%d' % data[i][j][0]+','+ \
					'%.2f' % data[i][j][1]+','+ \
					'%.2f' % (data[i][j][1]/data[i][j][0] if data[i][j][0]>0 else 0.0)+','+ \
					'%d' % (len(data[i][j][2])+len(data[i][j][3]))+','+ \
					'%d' % len(data[i][j][2])+','+ \
					'%d' % len(data[i][j][3])
					).encode('utf-8')

