#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, datetime, random
import app_helper
from config import setting

db = setting.db_web

url = ('/wx/red_envelope_1017')

# 红包设置
HB = { # hb_id : [begin_date, end_date, max_money]
	'002' : ['2015-10-19', '2015-10-21', 200000],
}

pool_size = {
	'2015-10-18' : { 'new': 50, 'old1': 100, 'old2': 100 },
	'2015-10-19' : { 'new': 2500000, 'old1': 1800000, 'old2': 700000 },
	'2015-10-20' : { 'new': 1500000, 'old1': 1050000, 'old2': 450000 },	
	'2015-10-21' : { 'new': 1000000, 'old1':  750000, 'old2': 250000 },
}

old_pool = [30, 30, 30, 30, 30, 30, 30, 50, 50, 50]

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
				# 检查已领金额
				sum0 = list(db.hb_store.aggregate([
					{'$match':{'hb_id':param.hb_id}},
					{'$group':{'_id':'0', 'sum':{'$sum':"$hb_new"}}}
				]))
				if len(sum0)==0:
					sum1=0
				else:
					sum1=sum0[0]['sum']
				print 'sum_new = ', sum0

				if sum1>pool_size[todate]['new']:
					return json.dumps({'ret' : -5, 'msg' : '红包发完'})

				hb_money = 40

				#插入操作
				#得到当前时间
				now_time = app_helper.time_str()
				db.hb_store.insert_one({
					'hb_id'         : '002', 
					"phone"         : param.phone_num.strip(), 
					"received_time" : now_time, 
					"hb_money"      : hb_money, 
					"hb_new"        : hb_money,
					"expired_date"  : ''})
			else:
				# 老用户先抽奖
				hb_money = old_pool[random.randint(0,9)]

				if hb_money==30:
					tag='old1'
				else:
					tag='old2'

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
					'hb_id'         : '002', 
					"phone"         : param.phone_num.strip(), 
					"received_time" : now_time, 
					"hb_money"      : hb_money, 
					"hb_%s"%tag     : hb_money,
					"expired_date"  : ''})

				# 老用户用户，立刻检查是否有新红包
				app_helper.check_hb(param.phone_num.strip())

			return json.dumps({'ret':0,'money':hb_money})


