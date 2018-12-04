#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from config import setting
import helper

db = setting.db_web

url = ('/pos/invent_update_price')

# 更新称重的商品售价  
class handler:        #class PosInventUpdatePrice:  
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_INVENTORY'):
			#render = helper.create_render()

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 取得 w-prod 的对应 u-prod 及其他信息
			db_invent=db.inventory.find({
				'shop'       : db_shop['shop'],
				'product_id' : { '$regex' : 'w.*', '$options' : 'i' },
				'num'        : { '$gt': 0 },
			}, {'ref_prod_id':1, 'product_id':1, 'weight':1})

			u_prod_id = []
			w_prod_id = []
			for i in db_invent:
				u_prod_id.append(i['ref_prod_id'])
				w_prod_id.append((i['product_id'],i['weight'],i['ref_prod_id']))
			#print u_prod_id

			# 取得 对应 u-prod 的单价
			db_invent2=db.inventory.find({
				'shop'       : db_shop['shop'],
				'product_id' : { '$in' : u_prod_id},
			}, {'price' : 1, 'product_id':1})

			new_price = {}
			for i in db_invent2:
				new_price[i['product_id']]=i['price']
			#print new_price

			# 更新 w-prod 的单价和称重售价
			for i in w_prod_id:
				db.inventory.update_one({
						'product_id' : i[0],
						'shop'       : db_shop['shop'],
					}, {
						'$set' : {
							'price' : new_price[i[2]], 
							'total' : '%.2f' % (float(i[1])*float(new_price[i[2]]))
						},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'价格修改为 %s' % str(new_price[i[2]]))},
					}
				)

			raise web.seeother('/pos/inventory?is_pack=w&show=1')
		else:
			raise web.seeother('/')
