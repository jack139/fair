#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos')

# 销货 ----------
class handler:        #class PosPos:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_POS'):
			render = helper.create_render(plain=True)
			#user_data=web.input(is_pack='1')

			# 查找
			db_shop = helper.get_shop_by_uid()
			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')
			#if db_shop2['type'] not in ['chain', 'store']:
			#	render = helper.create_render()
			#	return render.info('此站点不能线下销售！')

			return render.pos(helper.get_session_uname(), helper.get_privilege_name(), 
				db_shop2, helper.SHOP_TYPE)
		else:
			raise web.seeother('/')
