#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/online/order_detail')

# 返回订单cart内容
class handler:
	def POST(self):
		web.header("Content-Type", "application/json")
		result={'data':[], 'runner':[]}
		if helper.logged(helper.PRIV_USER,'ONLINE_MAN') or helper.logged(helper.PRIV_USER,'BATCH_JOB'):
			param = web.input(id='',order_id='')

			#if param.order_id=='t11511142049tcmcpx':
			#	print to_error

			# 查找门店
			db_shop = helper.get_shop_by_uid()

			# 门店名
			db_shop2 = db.base_shop.find_one({'_id':db_shop['shop']},{'name':1})
			shop_name = db_shop2['name']

			if len(param.order_id)>0:
				condition = {'order_id' : param.order_id}
			elif len(param.id)>0:
				condition = {'_id' : ObjectId(param.id)}
			else:
				return json.dumps({})

			# 查询订单详情
			db_todo=db.order_app.find_one(
				{'$and': [
					condition,
					{'shop' : db_shop['shop']},
				]}, 
				{ 'status':1, 'cart':1, 'lock':1, 'man':1, 'comment':1, 'due':1, 'user_note':1,
					'order_id':1, 'uname':1, 'address':1, 'paid_time':1, 'shop_0':1, 
					'type':1, 'region_id':1}
			)
			if db_todo!=None:
				if db_todo.get('type') in ['TUAN','SINGLE']: # 拼团
					for i in db_todo['cart']:
						result['data'].append({
							'product_id' : i['tuan_id'],
							'title'      : i.get('title','n/a'),
							'num'        : 1, # 固定 1
						})
					# 如果是拼团订单，站点名写实际发货站
					if str(db_shop['shop'])==setting.PT_shop[db_todo['region_id']] and db_todo.has_key('shop_0'):
						db_shop2 = db.base_shop.find_one({'_id':db_todo['shop_0']},{'name':1})
						shop_name = u'PT-'+db_shop2['name']
				else: # 1小时
					for i in db_todo['cart']:
						result['data'].append({
							'product_id' : i['product_id'],
							'title'      : i['title'],
							'num'        : i['num2']+i.get('numyy',0), #实际可购买数量+赠品数量
						})
				# 如果是整箱预售订单，站点名写实际发货站
				#if str(db_shop['shop'])==setting.B3_shop and db_todo.has_key('shop_0'):
				#	db_shop2 = db.base_shop.find_one({'_id':db_todo['shop_0']},{'name':1})
				#	shop_name = u'B3-'+db_shop2['name']


			print shop_name.encode('utf-8')

			result['num']=len(result['data'])

			# 查询快递员
			db_runner=db.user.find({'shop':db_shop['shop']}, 
				{'uname':1,'full_name':1,'privilege':1}).sort([('last_go',1)])
			for u in db_runner:
				if int(u['privilege'])&helper.PRIV_DELIVERY:
					result['runner'].append({
						'uname' : u['uname'],
						'full_name'  : u['full_name'],
					})
			result['runner_to_go'] = result['runner'][0]['uname'] # 用第一个快递员，已按last_go时间排序
			result['order_id'] = db_todo['order_id'] # 订单号
			# 合并返回地址, 对v3地址 2015-10-24
			if len(db_todo['address'])>=9: 
				new_addr = u'%s-%s(%s %s)' % (db_todo['address'][8],db_todo['address'][3],db_todo['address'][6],db_todo['address'][7])
			else:
				new_addr = db_todo['address'][3]
			#result['address'] = db_todo['address'] # 收货地址
			result['address'] = [db_todo['address'][0],db_todo['address'][1],db_todo['address'][2],new_addr] # 收货地址
			result['shop'] = shop_name # 站点名
			# paid_time会返回None， b3订单 2015-10-20
			result['paid_time'] = (u'' if db_todo.get('paid_time', u'')==None else db_todo.get('paid_time', u''))
			result['due'] = db_todo['due'] + u' 元'
			result['user_note'] = db_todo.get('user_note', '')

		#print result
		return json.dumps(result)

