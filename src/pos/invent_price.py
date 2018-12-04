#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/invent_price')

# 与 fair.py 里相同
def my_crypt(codestr):
	import hashlib
	return hashlib.sha1("sAlT139-"+codestr).hexdigest()

# 指定sku门店价格、及app的信息，根据type区分 2015-08-12
# type in ['price', 'category', 'list_in_app', 'sort_weight']
class handler:        #class PosInventPrice: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_INVENTORY'):
			user_data=web.input(product_id='', type='', price='', category='', list_in_app='', sort_weight='', passwd='')

			if '' in (user_data.product_id, user_data.type):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			if user_data.type=='price':
				r0 = db.user.find_one({'uname':setting.change_price},{'passwd':1})
				if r0:
					pwd = r0['passwd']
				else:
					pwd = my_crypt('_9412')
				if my_crypt(user_data.passwd)!=pwd:
					return json.dumps({'ret' : -4, 'msg' : '密码错误！'})

				f_price = float(user_data.price)

				db_invent=db.inventory.update_one({
						'product_id' : user_data.product_id, 
						'shop'       : db_shop['shop'],
					}, {
						'$set':{'price' : '%.2f' % f_price},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'价格修改为 %.2f' % f_price)},
					}
				)
			elif user_data.type=='category':
				db_invent=db.inventory.update_one({
						'product_id' : user_data.product_id, 
						'shop'       : db_shop['shop'],
					}, {
						'$set':{'category' : user_data.category},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'商品类目修改为 %s' % helper.CATEGORY[user_data.category])},
					}
				)
			elif user_data.type=='list_in_app':
				db_invent=db.inventory.update_one({
						'product_id' : user_data.product_id, 
						'shop'       : db_shop['shop'],
					}, {
						'$set':{'list_in_app' : int(user_data.list_in_app)},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'App销售修改为 %d' % int(user_data.list_in_app))},
					}
				)
			elif user_data.type=='sort_weight':
				db_invent=db.inventory.update_one({
						'product_id' : user_data.product_id, 
						'shop'       : db_shop['shop'],
					}, {
						'$set':{'sort_weight' : int(user_data.sort_weight)},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'App排序权重改为 %d' % int(user_data.sort_weight))},
					}
				)
			else:
				return json.dumps({'ret' : -2, 'msg' : 'type参数错误'})

			return json.dumps({'ret' : 0, 'msg' : '操作完成'})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
