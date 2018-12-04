#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper, jpush

db = setting.db_web

url = ('/delivery/order_view')

class handler:
	def GET(self):
		if helper.logged(helper.PRIV_DELIVERY,'DELVERY_ORDER'):
			render = helper.create_render(globals={'str':str})
			user_data=web.input(order='', status='')

			if '' in (user_data.order, user_data.status):
				return render.info('错误的参数！')  

			# 查找门店
			db_shop = helper.get_shop_by_uid()

			# 查询工单信息
			db_order=db.order_app.find_one({
				'order_id' : user_data.order,
				'shop' : ObjectId(db_shop['shop'])
			})
			if db_order==None:
				return render.info('order错误的参数！')  

			# 查询 站点信息
			s=db.base_shop.find_one({'_id':db_shop['shop']}, {'name':1, 'type':1})
			shop_name= '%s（%s）' % (s['name'].encode('utf-8'), helper.SHOP_TYPE[s['type']])

			return render.delivery_order_view(helper.get_session_uname(), helper.get_privilege_name(),
				db_order, shop_name, user_data.status, helper.ORDER_STATUS, db_order['history'])
		else:
			raise web.seeother('/')

	def POST(self): # 发货处理
		if helper.logged(helper.PRIV_USER,'DELVERY_ORDER'):
			render = helper.create_render()
			user_data=web.input(order='', next_status='')

			if '' in (user_data.order, user_data.next_status):
				return render.info('参数错误！')


			# 查找门店
			db_shop = helper.get_shop_by_uid()

			# 更新订单状态，进入派送
			r = db.order_app.find_one_and_update({
					'order_id' : user_data.order,
					'shop'     : db_shop['shop'],
					'status'   : { '$ne' : user_data.next_status },
				}, 
				{
					'$set' : {
						'status'  : user_data.next_status,
						'man'     : 0,
						'comment' : '',
					},
					'$push' : {'history' : (helper.time_str(), 
						helper.get_session_uname(), u'状态转换为'+user_data.next_status)}
				},
				{'_id':1, 'status':1, 'uname':1}
			)

			if r:
				# 推送通知
				if len(r['uname'])==11 and r['uname'][0]=='1':
					#if user_data.next_status=='DISPATCH':
					#	text = '您的订单已拣货完成，准备派送。'
					if user_data.next_status=='ONROAD':
						text = '您的订单开始派送，请等待收货。'
					#elif user_data.next_status=='COMPLETE':
					#	text = '您的订单派送成功。'
					else:
						text = None
					if text!=None:
						jpush.jpush(text, r['uname'])

			return render.info('成功保存！','/delivery/order?status='+r['status'])
		else:
			raise web.seeother('/')
