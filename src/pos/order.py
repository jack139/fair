#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/order')

# 仓储管理 之 工单处理 -------------------
class handler:        #class PosOrder:
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render(globals={'str':str})

			# 查找所属shop
			db_shop = helper.get_shop_by_uid()

			db_order=db.order_stock.find({ '$or': [
				{'type' : 'SEND', 'shop_to' : db_shop['shop']},  # 发货单
				{'type' : 'BOOK', 'shop_to' : db_shop['shop']}  # 订货单
			]},{'type':1,'status':1,'history':1}).sort([('_id',-1)])
			return render.pos_order(helper.get_session_uname(), helper.get_privilege_name(), 
				db_order, helper.ORDER_STATUS)
		else:
		    raise web.seeother('/')