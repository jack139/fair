#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import helper, jpush

db = setting.db_web

url = ('/online/order_dispatch')

# 开始派送
class handler:
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'ONLINE_MAN') or helper.logged(helper.PRIV_USER,'BATCH_JOB'):
			param = web.input(id='',order_id='')

			if param.id=='' and param.order_id=='':
				return json.dumps({'ret':-1, 'msg':'参数错误'})

			# 查找门店
			db_shop = helper.get_shop_by_uid()

			condition = {
				'shop'    : db_shop['shop'],
				'status'  : 'DISPATCH',
			}
			if len(param.order_id)>0:
				condition['order_id'] = param.order_id
			elif len(param.id)>0:
				condition['_id'] = ObjectId(param.id)

			# 更新订单状态，进入派送
			r = db.order_app.find_one_and_update(condition,
				{
					'$set' : {
						'status'  : 'ONROAD',
						'man'     : 0,
						#'comment' : '',
					},
					'$push' : {'history' : (helper.time_str(), 
						helper.get_session_uname(), '开始派送')}
				},
				{'_id':1, 'uname':1}
			)

			if r:
				# 推送通知
				if len(r['uname'])==11 and r['uname'][0]=='1':
					jpush.jpush('水果君&零食君正欢快的向您奔来，准备与他们尽情的玩耍吧！掌柜承诺：19.9元包邮，不满意退款', r['uname'])

				return json.dumps({'ret':0,'msg':'开始派送','id':str(r['_id'])})
			else:
				return json.dumps({'ret':3,'msg':'订单状态不是待配送'})
		else:
			return json.dumps({'ret':-1,'msg':'无访问权限'})

