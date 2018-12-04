#!/usr/bin/env python
# -*- coding: utf-8 -*-
import hashlib
import urllib
import httplib
import  time
from cgi import FieldStorage
from bson.objectid import ObjectId
import json
import web

import app_helper, elm_helper
from config import setting

db = setting.db_web
db_rep = app_helper.db_rep


url = ('/app/(v2|v3)/elm_port')

now_time = time.time().__long__()

	
def u_new_order(order_id):
	order_app_db = db.order_app.find_one({'elm_order_id':order_id},{'order_id':1})
	if order_app_db:
		print 'elm ********* 订单已存在'
		return 'ok'
	else:
		restaurant_info_path_url = "/order/{0}/".format(order_id)
		method = 'GET'
		params = {}
		response = elm_helper.elm_port(restaurant_info_path_url,params,method)
		dict = json.loads(response)
		if dict['code'] == 200:
			print dict['data']
			detail = dict['data']['detail']
			#print dict['data']['restaurant_id']
			address = [
				'elm',
				dict['data']['consignee'],
				dict['data']['phone_list'][0],
				#dict['data']['address'],
				#dict['data']['address'].encode('utf-8')+'('+dict['data']['delivery_poi_address'].encode('utf-8')+')',
				dict['data']['delivery_poi_address'] if dict['data']['delivery_poi_address']!=None else dict['data']['address'],
			]
			status = 'PAID'
			'''根据restaurant_id查询shop_id'''
			shop_id = db_rep.shop_restaurant.find_one({'elm_restaurant_id':dict['data']['restaurant_id']},{'shop_id':1})
			print 'elm *********** shop_id: ',shop_id
			if shop_id==None:
				print 'elm ???????????? 未找到 restaurant_id'
				return 'error'
			order_id = 'e' + app_helper.get_new_order_id('ve') # 新订单号逻辑 2015-10-24
			delivery_fee = dict['data']['deliver_fee']
			first_disc = 0.0
			cost = 0.0
			first_disc = 0.0
			user = 'elm'
			due = dict['data']['original_price']
			history = [[dict['data']['created_at'],dict['data']['phone_list'][0],'饿了吗接单']]
			retry = 0
			#print dict['data']['created_at'],type(dict['data']['created_at'])
			e_time = int(time.mktime(time.strptime(dict['data']['created_at'],'%Y-%m-%d %H:%M:%S')))
			b_time = int(time.mktime(time.strptime(dict['data']['created_at'],'%Y-%m-%d %H:%M:%S')))
			coupon = []
			uname = 'elm'
			coupon_disc = 0.0
			comment = ''
			man = 0
			pay = dict['data']['original_price']
			paid_tick = int(time.mktime(time.strptime(dict['data']['created_at'],'%Y-%m-%d %H:%M:%S')))
			change = 0.0
			paid_time = dict['data']['created_at']
			deadline = int(time.mktime(time.strptime(dict['data']['created_at'],'%Y-%m-%d %H:%M:%S')))
			lock = 0
			next_status = ''
			paid2_tick = int(time.mktime(time.strptime(dict['data']['created_at'],'%Y-%m-%d %H:%M:%S')))
			paid2_time = dict['data']['created_at']
			pay_type = 'elm'
			user_note = dict['data']['description']

			cart = []
			elm_order_id = dict['data']['order_id']
			total = 0

			b2 = [] # C端商品 2015-10-09
			b3 = [] # B3整箱预售商品 2015-10-09
			b3_total = 0.0 # 2015-10-09
			for g2 in detail['group']:
				for g in g2: # 可能多个篮子
					'''根据shop_id和elm_food_id查询produc_id'''
					product_id_db = db_rep.product_category.find_one({'shop':shop_id['shop_id'],'elm_food_id':g['id']},{'product_id':1})
					if product_id_db==None:
						print 'elm ???????????? 未找到elm_food_id', g['id']
						return 'error'
					print 'elm *********** food_id: ',g['id']
					num = g['quantity']
					num2 = g['quantity']
					title = g['name']
					price = g['quantity']*g['price']
					total += price
					item = { 
						"cost"       :cost, 
						"product_id" : product_id_db['product_id'], 
						"num2"       : num2, 
						"title"      : title, 
						"price"      : price, 
						"num"        : num ,
						'elm_food_id': g['id']
					}
					#cart.append(item)

					# 记录销售量
					db.sku_store.update_one({'product_id' : item['product_id']},
						  {'$inc' : {'volume' : float(item['num2'])}}
					)

					r3 = db.sku_store.find_one({'product_id' : item['product_id']},
						 {'list_in_app':1})
					if r3['list_in_app']== -3: # B3商品不需要改库存 # -3 不启动B3销售 2015-10-27
						 b3_total += float(item['price'])
						 b3.append(item)
						 item['title'] = item['title']+u'（整箱预售，次日送达）'
						 b2.append(item)
						 continue

					# 买X送Y
					if item['product_id'] in app_helper.buy_X_give_Y.keys():
						print 'elm 买X送Y'
						numX = app_helper.buy_X_give_Y[item['product_id']][0]
						numY = app_helper.buy_X_give_Y[item['product_id']][1]
						item['numyy'] = int(item['num2']/numX)*numY  # 赠
					else:
						item['numyy'] = 0

					#if item['product_id'] in app_helper.buy_1_give_1:
					#	print '买一送一'
					#	lc_num2 = float(item['num2'])
					#	item['num2'] = int(lc_num2 + lc_num2)
					#	item['title'] = item['title'].replace(u'买一送一',u'特惠活动')

					# 过滤数量价格为零的
					if item['num2']==0 and float(item['price'])==0.0:
						continue

					# num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
					num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
					r2 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
						{
							'product_id' : item['product_id'],
							'shop'       : shop_id['shop_id'],
						},
						{ 
							'$inc'  : { 
								'num'         : 0-num_to_change, # num2 实际购买数量
								'pre_pay_num' : num_to_change, # 记录预付数量
							}
							#'$push' : { 'history' : (helper.time_str(), 
							#	helper.get_session_uname(), '售出 %s' % str(item['num']))},
						},
						{'_id':1}
					)
					#print r
					if r2==None: # 不应该发生
						 print 'elm *********** 修改库存失败，请联系管理员！'
						 return 'ok'
						 #return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
					else:
						 b2.append(item)

					#print shop_id['shop_id'],'==='
					#print product_id_db['product_id']
					#print g['id']

					# 更新elm库存数据
					app_helper.elm_modify_num(shop_id['shop_id'], item['product_id'])

			# 新的订单信息
			r = {
				'address'      : address,
				'b_time'       : b_time,
				'cart'         : b2, #cart,
				'comment'      : comment,
				'cost'         : '%.2f'%cost,
				'coupon'       : coupon,
				'coupon_disc'  : '%.2f'%coupon_disc,
				'deadline'     : deadline,
				'delivery_fee' : '%.2f'%delivery_fee,
				'due'          : '%.2f'%due,
				'e_time'       : e_time,
				'first_disc'   : '%.2f'%first_disc,
				'history'      : history,
				'lock'         : lock,
				'man'          : man,
				'next_status'  : next_status,
				'order_id'     : order_id,
				'order_source' : 'elm',
				'paid2_tick'   : paid2_tick,
				'paid2_time'   : paid2_time,
				'paid_tick'    : paid_tick,
				'paid_time'    : paid_time,
				'pay'          : '%.2f'%pay,
				'pay_type'     : pay_type,
				'retry'        : retry,
				'shop'         : shop_id['shop_id'],
				'status'       : status,
				'total'        : '%.2f'%total,
				'uname'        : uname,
				'user'         : user,
				'elm_order_id' : elm_order_id,
				'user_note'    : user_note,
				'type'           : 'HOUR',
				'credit_total'   : '0.00', # 余额支付金额 2015-11-24
				'wxpay_total'    : '0.00', # 微信支付金额 
				'alipay_total'   : '0.00', # 支付宝支付金额 
				'use_credit'     : '0.00', # 部分支付时，余额支付金额
				'due3'           : '0.00', # 第3方应付金额   use_credit + due3 = due
			}

			# 检查是否有b3商品, 3种情况
			# 1. b2, b3 都有，拆单
			# 2. 只有b3，站点改为B3站点，保留收货站点
			# 3. 只有b2，保持订单不变
			#print b2
			#print b3
			if len(b3)>0 and (len(b2)-len(b3))>0: # 情况1
				print "elm 拆单"
				r4 = r.copy()
				r4['order_id']     = r4['order_id']+u'-b3'
				r4['shop_0']       = r['shop']
				r4['shop']         = ObjectId(setting.B3_shop)
				r4['cart']         = b3
				r4['status']       = status
				r4['elm_order_id'] = elm_order_id # 饿了吗 订单号
				r4['paid_time']    = app_helper.time_str()
				r4['paid_tick']    = int(time.time())
				r4['history']      = [(app_helper.time_str(), 'elm_port', 'elm－拆单')]
				r4['total']        = '%.2f' % b3_total
				r4['cost']         = '0.00'
				r4['coupon_disc']  = '0.00'
				r4['first_disc']   = '0.00'
				r4['delivery_fee'] = '0.00'
				r4['due']          = '0.00'
				db.order_app.insert_one(r4) # 增加子订单
			elif len(b3)>0: # 情况 2
				print "elm 订单改到B3站点"
				db.order_app.update_one({'order_id':order_id},{'$set' : {
					'shop_0' : r['shop'],
					'shop'   : ObjectId(setting.B3_shop),
				}})
			else: # 情况3，什么都不做
				print "elm 订单保持不变"

			print  'elm *********** order_id: ',order_id
			'''将查询的订单详情插入U掌柜数据库中'''
			db.order_app.insert_one(r)
			return 'ok'
		else:
			print 'elm ???????????? elm 订单拉取失败'
			print dict
			return 'error'
		
def modify_order_status(order_id):
	restaurant_info_path_url = "/order/{0}/status/".format(order_id)
	method = 'PUT'
	params = {}
	params['status'] = 2
	elm_helper.elm_port(restaurant_info_path_url,params,method)
		
class handler:
	def GET(self, version='v2'):
		print 'elm ============== GET'
		return json.dumps({'message':'ok','code':200})
	def POST(self, version):
		print 'version', version
		consumer_key = '3806191616'
		consumer_secret = '6dc6dba638b3da975464055a7d227854cb66776b'
		path_url = '/platform3/elm_port'
		print 'elm ============== elm 订单'
		system_params = {}
		system_params['consumer_key'] = consumer_key
		system_params['timestamp'] = now_time
		params = {}
		all_params = dict(params, **system_params)
		sig = elm_helper.gen_sig(path_url, all_params, consumer_secret)
		
		
		
		'''验证sig'''
		header_type = web.ctx.env.get('CONTENT_TYPE')
		path_w = web.ctx.env['PATH_INFO']
		query_str = web.ctx.env['QUERY_STRING']
		consumer_key_w = query_str.rsplit('=', 1)[-1]
		system_params_w = {}
		system_params_w['consumer_key'] = int(consumer_key_w)
		system_params_w['timestamp'] = now_time
		params_w = {}
		all_params_w = dict(params_w, **system_params_w)
		sig_w = elm_helper.gen_sig(path_url, all_params_w, consumer_secret)
		
		if sig != sig_w:
			print 'elm ==================== sig error!'
			return json.dumps({'message':'error','code':1001})
		else:
			data = web.input()
			print 'elm =================== sig pass'
			print data
			push_action = data['push_action']
			if push_action == '1':
				order_list = (data['eleme_order_ids'].encode('UTF-8')).split(',')
				print 'elm ========== order_list: ',order_list
				s = 0
				for i in order_list:
					#新建订单
					res = u_new_order(i)
					if res == 'error':
						print 'elm ?????????? u_new_order: error', i
						s = 1
					else:
						'''根据订单id修改订单状态'''
						print 'elm ======== elm 接单确认'
						modify_order_status(i)

				if s == 0:
					return {'message':'ok','code':200}
				else:
					return {'message':'error','code':1004}
			if push_action == '2':
				print 'elm ========== order_id: ',data['eleme_order_id']
				order_status = db.order_app.find_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},{'status':1})
				'''判断elm推送的状态，修改本地数据库的状态'''
				if order_status:
					if data['new_status'] == '0':#订单未处理
						print 'elm ========================= 订单未处理'
						#db.order_app.update_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},{'$set':{'status':'CANCEL1', 'man':1}})
					elif data['new_status'] == '-1':#订单已取消
						print 'elm ========================= 订单已取消'
						'''查询订单当前状态'''
						if order_status['status'] == 'PAID':
							db.order_app.update_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},{'$set':{'status':'CANCEL2', 'man':1}})
						if order_status['status'] == 'DISPATCH':
							db.order_app.update_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},{'$set':{'status':'CANCEL3', 'man':1}})
						if order_status['status'] == 'ONROAD':
							db.order_app.update_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},{'$set':{'status':'CANCEL4', 'man':1}})
					elif data['new_status'] == '2':#订单已处理
						print 'elm ========================= 订单已处理'
						#if order_status['status'] == 'GAP':
						#	'''取消订单'''
						#	restaurant_info_path_url = "/order/{0}/status/".format(data['eleme_order_id'].encode('utf-8'))
						#	method = 'PUT'
						#	params = {}
						#	params['status'] = -1
						#	params['reason'] = '库存不足'
						#	elm_helper.elm_port(restaurant_info_path_url,params,method)

					#记录历史
					db.order_app.update_one({'elm_order_id':data['eleme_order_id'].encode('utf-8')},
						{'$push':{'history':(
							app_helper.time_str(),
							'elm_port',
							'新elm订单状态 %s' % data['new_status'].encode('utf-8')
						)}}
					)

				return json.dumps({'message':'ok','code':200})
			
