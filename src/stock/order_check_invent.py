#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/stock/order_check_invent')

# 返回 工单中商品的库存信息
class handler:      
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'STOCK_ORDER'):
			user_data=web.input(shop='', order='')

			if '' in (user_data.shop, user_data.order):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 取得工单数据
			db_order = db.order_stock.find_one({'_id':ObjectId(user_data.order)},{'cart':1})
			if db_order==None:
				return render.info('未找到订单数据！')

			pids={}
			for i in db_order['cart']:
				pids[i['product_id']]=0

			if user_data.shop=='-': # 未选择仓库
				return json.dumps({'ret' : 0, 'data' : pids})

			# 查库存信息
			db_invent=db.inventory.find({
				'product_id' : {'$in' : pids.keys()}, 
				'shop'       : ObjectId(user_data.shop),
			}, {'product_id':1, 'num':1})

			for i in db_invent:
				pids[i['product_id']]=i['num']

			return json.dumps({'ret' : 0, 'data' : pids})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})

