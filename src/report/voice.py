#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/report/voice')

# - 用户反馈 －－－－－－－－－－－
class handler:        #class PosReport:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'REPORT_VOICE'):
			render = helper.create_render()
			#user_data=web.input(start_date='', shop='__ALL__', ret_type='table')
			
			# 显示最近30天的
			start_date = helper.time_str(time.time()-3600*24*30, format=1)

			# 起至时间
			begin_date = '%s 00:00:00' % start_date
			#end_date = '%s 23:59:59' % start_date

			#print begin_date, end_date

			# 
			db_voice = db.customer_voice.find({'time' : {'$gt' : begin_date}},{'_id':0}).sort([('_id',-1)])

			return render.report_voice(helper.get_session_uname(), helper.get_privilege_name(), db_voice)
		else:
			raise web.seeother('/')


