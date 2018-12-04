#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper, jpush

db = setting.db_web

url = ('/plat/push_msg')

class handler:   #class PlatBaseSku:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'APP_PUSH'):
			render = helper.create_render()
			return render.jpush(helper.get_session_uname(), helper.get_privilege_name())
		else:
		    raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'APP_PUSH'):
			render = helper.create_render()
			user_data=web.input(phone='',content='')

			if user_data.phone.strip()=='': # 发送全部
				r=jpush.jpush(user_data.content)
				#r = False # 测试时关闭全部发送
			else:
				# 发送指定号码，最多1000个号码
				r=jpush.jpush(user_data.content, user_data.phone)

			# 记录发送日志
			db.jpush_log.insert({ 
				'push_time' : helper.time_str(),
				'user'      : helper.get_session_uname(),
				'phone'     : user_data.phone.strip(),
				'content'   : user_data.content,
				'result'    : r
			})

			if r!=False:
				return render.info('发送成功！ '+r,'/plat/push_msg')
			else:
				return render.info('发送失败！','/plat/push_msg')
		else:
		    raise web.seeother('/')