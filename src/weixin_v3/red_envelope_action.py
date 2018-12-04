#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, datetime, random
import app_helper
from config import setting

db = setting.db_web

url = ('/wx/red_envelope_action')

# 修改收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(phone_num='',hb_id='')
		#print param

		if '' in (param.phone_num, param.hb_id):
			return json.dumps({'ret' : -1, 'msg' : '参数错误'})

		if not app_helper.HB.has_key(param.hb_id):
			return json.dumps({'ret' : -2, 'msg' : 'hb_id参数错误'})

		# 检查活动时间
		now_date = datetime.datetime.now()
		todate = now_date.strftime('%Y-%m-%d')
		if todate<app_helper.HB[param.hb_id][0] or todate>app_helper.HB[param.hb_id][1]:
			return json.dumps({'ret' : -3, 'msg' : '活动过期'})

		# 检查已领金额
		sum0 = list(db.hb_store.aggregate([
			{'$match':{'hb_id':param.hb_id}},
			{'$group':{'_id':'0', 'sum':{'$sum':"$hb_money"}}}
		]))
		if len(sum0)==0:
			sum1=0
		else:
			sum1=sum0[0]['sum']
		print 'sum = ', sum0

		if sum1>app_helper.HB[param.hb_id][2]:
			return json.dumps({'ret' : -5, 'msg' : '红包发完'})

		# 检查号码是否已领
		red_envelope_db = db.hb_store.find_one({'phone':param.phone_num},{'phone':1})
		#如果不存在则插入，存在则提醒已存在
		if red_envelope_db:
			return json.dumps({'ret':-4, 'msg' : '已领红包'})
		else:
			#插入操作
			#得到当前时间
			now_date = datetime.datetime.now()
			overdue_time = (now_date+datetime.timedelta(days=7)).strftime('%Y-%m-%d')
			now_time = now_date.strftime('%Y-%m-%d %H:%M:%S')
			env_money = random.randint(2,5)
			db.hb_store.insert_one({
				'hb_id'         : param.hb_id, 
				"phone"         : param.phone_num, 
				"received_time" : now_time, 
				"hb_money"      : env_money, 
				"expired_date"  : overdue_time})

			# 检查是否有新红包
			app_helper.check_hb(param.phone_num)

			return json.dumps({'ret':0,'money':env_money})


