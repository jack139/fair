#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, datetime, random
import app_helper
from config import setting

db = setting.db_web

url = ('/wx/red_envelope_1111')

# 红包设置
HB = { # hb_id : [begin_date, end_date, max_money]
	'003' : ['2015-11-10', '2015-11-13', 200000],
}

pool_size = {
	'2015-11-10' : { 'new': 50, 'old': 100, 'wb': 19.80 },
	'2015-11-11' : { 'new': 600000, 'old': 900000, 'wb': 1980 },
	'2015-11-12' : { 'new': 600000, 'old': 900000, 'wb': 1980 },	
	'2015-11-13' : { 'new': 600000, 'old': 900000, 'wb': 1980 },
}

#old_pool = [30, 30, 30, 30, 30, 30, 30, 50, 50, 50]

# 修改收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(phone_num='',hb_id='')
		#print param

		if '' in (param.phone_num, param.hb_id):
			return json.dumps({'ret' : -1, 'msg' : '参数错误'})

		if not HB.has_key(param.hb_id):
			return json.dumps({'ret' : -2, 'msg' : 'hb_id参数错误'})

		# 检查活动时间
		todate = app_helper.time_str(format=1)
		if todate<HB[param.hb_id][0] or todate>HB[param.hb_id][1]:
			return json.dumps({'ret' : -3, 'msg' : '活动过期'})

		# 检查号码是否已领
		red_envelope_db = db.hb_store.find_one({'hb_id':param.hb_id,'phone':param.phone_num.strip()},{'phone':1})
		#如果不存在则插入，存在则提醒已存在
		if red_envelope_db:
			return json.dumps({'ret':-4, 'msg' : '已领红包'})
		else:
			# 是否是新客
			new_user = db.app_user.find_one({'uname':param.phone_num.strip()})==None

			if new_user:
				# 抽奖
				if random.randint(0,100)==11:
					hb_money = 19.80
					tag='wb'
				else:
					hb_money = 20
					tag='new'

				# 检查已领金额
				sum0 = list(db.hb_store.aggregate([
					{'$match':{'hb_id':param.hb_id}},
					{'$group':{'_id':'0', 'sum':{'$sum':"$hb_%s"%tag}}}
				]))

				if len(sum0)==0:
					sum1=0
				else:
					sum1=sum0[0]['sum']
				print 'sum_%s = '%tag, sum0

				if sum1>pool_size[todate][tag]:
					return json.dumps({'ret' : -5, 'msg' : '红包发完'})

				#插入操作
				#得到当前时间
				now_time = app_helper.time_str()
				db.hb_store.insert_one({
					'hb_id'         : '003', 
					"phone"         : param.phone_num.strip(), 
					"received_time" : now_time, 
					"hb_money"      : hb_money, 
					"hb_%s"%tag     : hb_money,
					"expired_date"  : ''})
			else:
				# 老用户先抽奖
				if random.randint(0,100)==11:
					hb_money = 19.8
					tag='wb'
				else:
					hb_money = 30
					tag='old'

				# 检查已领金额
				sum0 = list(db.hb_store.aggregate([
					{'$match':{'hb_id':param.hb_id}},
					{'$group':{'_id':'0', 'sum':{'$sum':"$hb_%s"%tag}}}
				]))
				if len(sum0)==0:
					sum1=0
				else:
					sum1=sum0[0]['sum']
				print 'sum_%s = '%tag, sum0

				if sum1>pool_size[todate][tag]:
					return json.dumps({'ret' : -5, 'msg' : '红包发完'})

				#插入操作
				#得到当前时间
				now_time = app_helper.time_str()
				db.hb_store.insert_one({
					'hb_id'         : '003', 
					"phone"         : param.phone_num.strip(), 
					"received_time" : now_time, 
					"hb_money"      : hb_money, 
					"hb_%s"%tag     : hb_money,
					"expired_date"  : ''})

				# 老用户用户，立刻检查是否有新红包
				app_helper.check_hb(param.phone_num.strip())

			return json.dumps({'ret':0,'money':hb_money})


