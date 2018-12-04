#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/online/man')

# 线上订单处理
class handler:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'ONLINE_MAN'):
			render = helper.create_render()
			# 查找门店
			db_shop = helper.get_shop_by_uid()
			shop_name = helper.get_shop(db_shop['shop'])

			if str(db_shop['shop']) in setting.PT_shop.values():
				pt_shop = True
			else:
				pt_shop = False
			print 'pt_shop = ', pt_shop
			return render.online_man(helper.get_session_uname(), helper.get_privilege_name(),shop_name['name'],pt_shop)
		else:
			raise web.seeother('/')
