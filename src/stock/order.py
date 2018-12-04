#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/stock/order')

# 仓储管理 之 工单处理 -------------------
class handler:        #class StockOrder:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'STOCK_ORDER'):
			render = helper.create_render(globals={'str':str})

			db_order=db.order_stock.find({},
				{'shop_to':1,'type':1,'status':1,'history':1},
				#limit = 100
			).sort([('_id',-1)])

			db_shops=db.base_shop.find({},{'name':1})
			shops={}
			for i in db_shops:
				shops[i['_id']]=i['name']
			return render.stock_order(helper.get_session_uname(), helper.get_privilege_name(), 
				db_order, helper.ORDER_STATUS, shops)
		else:
		    raise web.seeother('/')