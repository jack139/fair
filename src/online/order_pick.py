#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import helper, jpush

db = setting.db_web

url = ('/online/order_pick')

# 返回订单cart内容
class handler:
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'ONLINE_MAN') or helper.logged(helper.PRIV_USER,'BATCH_JOB'):
			param = web.input(order_id='', ok='', runner='')

			if '' in (param.order_id, param.ok, param.runner):
				return json.dumps({'ret':-1, 'msg':'参数错误'})

			# 查找
			db_shop = helper.get_shop_by_uid()

			if param.ok!='1': # 拣货失败，部分缺货
				r = db.order_app.find_one_and_update({
						'order_id' : param.order_id,
						'shop'     : db_shop['shop'],
					}, {
						'$set' : {
							'status'  : 'GAP',
							'man'     : 1,
							'comment' : '0|PAID|部分缺货'
						},
						'$push' : {
							'history'  : (helper.time_str(), 
								helper.get_session_uname(), '部分缺货')
						}
					}, 
					{'_id':1}
				)
				return json.dumps({'ret':0,'msg':'提交部分缺货','id':str(r['_id'])})

			# 查询快递员
			db_runner=db.user.find_one({'shop':db_shop['shop'], 'uname':param.runner}, 
				{'uname':1,'full_name':1})
			runner_info = db_runner['full_name'].split('|') # [name, tel]
			if len(runner_info)<2:
				runner_info.append('未知')

			# 更新订单状态，进入派送
			r = db.order_app.find_one_and_update({
				'order_id' : param.order_id,
				'shop'     : db_shop['shop'],
				'status'   : 'PAID',
			}, {
				'$set' : {
					'status'  : 'DISPATCH',
					'runner'  : {
						'uname' : db_runner['uname'], 
						'name'  : runner_info[0], 
						'tel'   : runner_info[1],
					},
					#'comment' : '',
				},
				'$push' : {
					'history'  : (helper.time_str(), 
							helper.get_session_uname(), '拣货完成')
				}
			}, {'_id':1, 'uname':1})

			if r:
				# 推送通知
				#if len(r['uname'])==11 and r['uname'][0]=='1':
				#	jpush.jpush('您的订单已拣货完成，准备派送。', r['uname'])

				# 查询订单详情
				db_todo=db.order_app.find_one(
					{'$and': [
						{'order_id' : param.order_id},
						{'shop'     : db_shop['shop']},
					]}, 
					{ 'status':1, 'cart':1, 'lock':1, 'man':1, 'comment':1, 'order_id':1, 'uname':1, 'type':1}
				)
				if db_todo!=None:
					if db_todo.get('type') in ['TUAN','SINGLE']: # 拼团增加销量
						db.pt_store.update({'tuan_id':db_todo['cart'][0]['tuan_id']},
							{'$inc':{'volume':1}})
					else:
						# 修改库存，pre_pay_num
						for i in db_todo['cart']:
							db.inventory.update_one({
								'product_id' : i['product_id'],
								'shop'       : db_shop['shop'],
							}, {'$inc' : {'pre_pay_num' : 0-i['num2']}})

				return json.dumps({'ret':0,'msg':'提交拣货完成','id':str(r['_id'])})
			else:
				return json.dumps({'ret':-3,'msg':'订单状态不是待拣货'})
		else:
			return json.dumps({'ret':-1,'msg':'无访问权限'})

