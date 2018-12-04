#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, re
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/online/batch_paid')

# - 批量处理paid订单
class handler: 
	def GET(self):
		if helper.logged(helper.PRIV_USER,'BATCH_JOB'):
			render = helper.create_render()
			user_data=web.input(tuan_id='',sheng='')

			# 查找shop
			db_shop = helper.get_shop_by_uid()
			shop_name = helper.get_shop(db_shop['shop'])

			# 统计线上订单
			condition = {
				'shop'   : db_shop['shop'],
				'status' : 'PAID',
				'type'   : {'$in': ['TUAN', 'SINGLE']}, # 目前只拼团用
				'address.8' : re.compile('^%s.*' % user_data.sheng.strip().encode('utf-8'))
			}

			db_sale2 = db.order_app.find(condition, {
				'order_id'  : 1,
				'paid_time' : 1,
				'cart'      : 1,
				'type'      : 1,
				'status'    : 1,
				'address'   : 1, 
			}).sort([('_id',1)])

			r = db.pt_store.find_one({'tuan_id':user_data['tuan_id']},{'title':1})
			if r:
				title = r['title']
			else:
				title = 'n/a'

			skus=[]
			count=0
			for i in db_sale2:
				if i['cart'][0]['tuan_id']!=user_data['tuan_id']:
					continue
				else:
					# 只记录知道活动的订单号
					skus.append(i['order_id'])
					count += 1
					if count==100: # 一次只处理100个
						break

			return render.batch_paid(helper.get_session_uname(), helper.get_privilege_name(), 
				skus, len(skus), shop_name, user_data['tuan_id'], title, user_data['sheng'])
		else:
			raise web.seeother('/')


