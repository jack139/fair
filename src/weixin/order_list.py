#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, helper

db = setting.db_web

url = ('/wx/order_list')

QUERY = {
	'DUE'  : 'DUE',
	'PAID' : 'PAID',
	'ROAD' : 'ONROAD',
	'CMPL' : 'COMPLETE',
	'CANC' : 'CANCEL'
}

# 订单列表
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', query='')

		if param.query=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_user = db.app_user.find_one({'openid':uname['openid']},{'coupon':1, 'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 修改为付款的过期订单
			r = db.order_app.update_many({
				'uname'    : {'$in' : uname.values()},
				'status'   : 'DUE',
				'deadline' : {'$lt':int(time.time())}
			}, {'$set': {'status':'TIMEOUT'}})
			#print r

			# 获得订单
			if param.query=='ALL':
				condition = {'user' : {'$in' : uname.values()}, 'status':{'$ne':'TIMEOUT'}}
			else:
				condition = {
					'user'   : {'$in' : uname.values()},
					'status' : QUERY.get(param.query)
				}
			db_order = db.order_app.find( condition,
				{'status':1, 'cart':1, 'due':1, 'shop':1, 'history':1, 'order_id':1, 'deadline':1}
			).sort([('order_id',-1)])
			order_list=[]
			for i in db_order:
				# 取购物车中第一个商品的图片
				db_sku = db.sku_store.find_one({'product_id':i['cart'][0]['product_id']},
					{'base_sku':1})
				base_sku = db.dereference(db_sku['base_sku'])
				image = base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else ''
				order_list.append({
					'order_id'   : i['order_id'],
					'order_time' : i['history'][0][0], 
					'image'      : '/%s/%s' % (image[:2], image),
					'status'     : helper.ORDER_STATUS['APP'].get(i['status'], '未知状态'),
					'due'        : i['due'],
					'count'      : len(i['cart']),
				})

			return json.dumps({
				'ret'  : 0, 
				'data' : { 
					'order_list' : order_list,
					'credit'     : '%.2f' % db_user.get('credit', 0.0)
				}
			})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
