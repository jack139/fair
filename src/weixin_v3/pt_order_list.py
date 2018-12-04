#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, helper

db = setting.db_web

url = ('/wx/pt_order_list')


# 我的拼团列表
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', region_id='', query='')

		if '' in (param.query, param.region_id):
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

			# 刷新订单状态，过期的OPEN活动变为FAIL1, 个人订单已付款的变为FAIL_TO_REFUND
			r2 = db.pt_order.find({
				'status'      : 'OPEN',
				'expire_tick' : {'$lt' : int(time.time()) }
			}, { 'pt_order_id':1 })
			for x in r2:
				# 已付款的已付款的变为FAIL_TO_REFUND
				db.order_app.update_many({'pt_order_id':x['pt_order_id'],'status':'PAID_AND_WAIT'},
					{
						'$set'  : {'status'  : 'FAIL_TO_REFUND', 'man' : 1},
						'$push' : {'history' : (app_helper.time_str(), 'system', '超时成团失败')}
					}
				)
				#过期的OPEN活动变为FAIL1,
				r3 = db.pt_order.find_one_and_update({'_id':x['_id']},
					{
						'$set'  : {'status'  : 'FAIL1'},
						'$push' : {'history' : (app_helper.time_str(), 'system', '超时成团失败')}
					},
					{'member':1}
				)
				print '发微信通知'
				for x in r3['member']:
					print app_helper.wx_reply_msg(x['openid'], '很抱歉，你参加的拼团活动已过24小时，人数不足未能成团，我们将在1-3个工作日内为您安排退款到支付帐户')


			# 获得订单
			#if param.query=='ALL':
			condition = {
				'region_id' : {'$in' : [ param.region_id ]},
				'$or' : [
					{'member.openid' : uname['openid']},
					{'leader'        : uname['openid']},
				],
			}

			image_host = 'http://%s/image/product' % setting.image_host

			db_pt_order = db.pt_order.find( condition ).sort([('_id',-1)])
			order_list=[]
			for i in db_pt_order:
				if i['status'] in ['WAIT','FAIL3']: # 未开团成功的团不显示
					continue
				if i['type']=='SINGLE': # 个人购买不显示
					continue

				# 取购物车中第一个商品的图片
				db_sku = db.pt_store.find_one({'tuan_id':i['tuan_id']})
				image = ['%s/%s/%s' % (image_host, x[:2], x) for x in db_sku['image']]
				# 取订单order_id
				r = db.order_app.find_one({
					'pt_order_id':i['pt_order_id'],
					'uname':uname['openid']
				}, {'order_id':1})
				if r==None:
					print 'Not found: ', i['pt_order_id']
					return json.dumps({'ret' : -5, 'msg' : '未找到order'})
				# 准备结果
				order_list.append({
					'tuan_id'     : i['tuan_id'], 
					'pt_order_id' : i['pt_order_id'], 
					'order_id'    : r['order_id'], # 订单order_id
					'title1'      : db_sku['title'], 
					'image'       : image,
					'status'      : i['status'],   
					'due'         : db_sku['tuan_price'],
					'type'        : '%d人团'%db_sku['tuan_size'],
				})

			#print order_list

			return json.dumps({
				'ret'  : 0, 
				'data' : { 
					'region_id'  : param.region_id,
					'order_list' : order_list,
				}
			})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
