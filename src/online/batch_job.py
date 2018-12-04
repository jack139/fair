#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/online/batch_job')

# - 批量处理订单
class handler: 
	def GET(self):
		if helper.logged(helper.PRIV_USER,'BATCH_JOB'):
			render = helper.create_render()
			#user_data=web.input(start_date='', shop='__ALL__')
			
			# 查找shop
			db_shop = helper.get_shop_by_uid()
			shop_name = helper.get_shop(db_shop['shop'])

			# 统计线上订单
			condition = {
				'shop'   : db_shop['shop'],
				'status' : {'$in' : ['PAID','DISPATCH','ONROAD']},
				'type'   : {'$in' : ['TUAN', 'SINGLE']}, # 只拼团用
			}

			db_sale2 = db.order_app.find(condition, {
				'order_id'  : 1,
				'paid_time' : 1,
				'cart'      : 1,
				'type'      : 1,
				'status'    : 1,
				'address'   : 1,
			})

			skus={}
			for i in db_sale2:
				# 区分省份
				sheng = i['address'][8].split(',')[0] if len(i['address'])>=9 else u'未知'
				if skus.has_key(i['cart'][0]['tuan_id']):
					if skus[i['cart'][0]['tuan_id']].has_key(sheng):
						skus[i['cart'][0]['tuan_id']][sheng]['num'] += 1
						skus[i['cart'][0]['tuan_id']][sheng]['paid'] += (1 if i['status']=='PAID' else 0)
						skus[i['cart'][0]['tuan_id']][sheng]['dispatch'] += (1 if i['status']=='DISPATCH' else 0)
						skus[i['cart'][0]['tuan_id']][sheng]['onroad'] += (1 if i['status']=='ONROAD' else 0)
					else:
						skus[i['cart'][0]['tuan_id']][sheng] = {}
						skus[i['cart'][0]['tuan_id']][sheng]['num'] = 1
						skus[i['cart'][0]['tuan_id']][sheng]['paid'] = (1 if i['status']=='PAID' else 0)
						skus[i['cart'][0]['tuan_id']][sheng]['dispatch'] = (1 if i['status']=='DISPATCH' else 0)
						skus[i['cart'][0]['tuan_id']][sheng]['onroad'] = (1 if i['status']=='ONROAD' else 0)
				else:
					r = db.pt_store.find_one({'tuan_id':i['cart'][0]['tuan_id']},{'title':1})
					if r:
						title = r['title']
					else:
						title = 'n/a'

					skus[i['cart'][0]['tuan_id']] = {
						'name'     : title,
						'tuan_id'  : i['cart'][0]['tuan_id'],					
					}
					skus[i['cart'][0]['tuan_id']][sheng]={
						'num'      : 1, # 要包含送的
						'paid'     : 1 if i['status']=='PAID' else 0, # 已付款，待拣货的， 拼团用
						'dispatch' : 1 if i['status']=='DISPATCH' else 0, # 已付款，待配送， 拼团用
						'onroad'   : 1 if i['status']=='ONROAD' else 0, # 已付款，配送中， 拼团用
					}

			total_sum={}
			for i in skus.keys():
				for j in skus[i].keys():
					if j in ['name','tuan_id']:
						continue
					if total_sum.has_key(j):
						total_sum[j]['paid'] += skus[i][j]['paid']
						total_sum[j]['dispatch'] += skus[i][j]['dispatch']
						total_sum[j]['onroad'] += skus[i][j]['onroad']
					else:
						total_sum[j] = {}
						total_sum[j]['paid'] = skus[i][j]['paid']
						total_sum[j]['dispatch'] = skus[i][j]['dispatch']
						total_sum[j]['onroad'] = skus[i][j]['onroad']

			return render.batch_job(helper.get_session_uname(), helper.get_privilege_name(), 
				skus, shop_name['name'], total_sum)
		else:
			raise web.seeother('/')


