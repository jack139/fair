#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import helper

db = setting.db_web

url = ('/online/order_check')

# 检查线上订单队列
class handler:
	def POST(self):
		result={'data':[]}
		if helper.logged(helper.PRIV_USER,'ONLINE_MAN'):
			# 查找门店
			db_shop = helper.get_shop_by_uid()

			# 查询订单信息
			db_todo=db.order_app.find(
				{'$and': [
					{'shop':db_shop['shop']},
					{'status' : {'$nin': ['FINISH','DUE','COMPLETE','TIMEOUT', 'CANCEL', 'REFUND']}},
					#{'event'  : {'$ne':'ORDER_API'}},
					{'lock'   : 0}
				]}, 
				{ 
					'status':1, 'b_time':1, 'e_time':1, 'lock':1, 'runner':1,
					'man':1, 'comment':1, 'order_id':1, 'uname':1, 'paid_time':1, 'paid_tick':1
				}
			).sort([('b_time',1)])  # 先下单的处理
			for todo in db_todo:					
				#start_tick = int(time.mktime(time.strptime(todo['trainStartTime'],"%Y-%m-%d %H:%M")))
				if todo['status'] in ['FAIL','PREPAID','CANCEL4','CANCEL3','CANCEL2','CANCEL1'] \
					and int(time.time())-todo['b_time']>172800:
					continue
				
				result['data'].append({
					'id'        : str(todo['_id']),
					'status'    : todo['status'],
					#'elapse'    : int(time.time())-todo.get('paid_tick',int(time.time())), #todo['e_time']-todo['b_time'],
					'lock'      : todo['lock'],
					'man'       : todo['man'],
					'user'      : todo['uname'],
					'comment'   : todo['comment'],
					'orderNo'   : todo['order_id'],
					'runner'    : todo['runner'] if todo.has_key('runner') else '',
					'paid_time' : todo.get('paid_time', 'n/a'),
					#'urgent'    : 1 if todo.has_key('paid_tick') and (int(time.time()-todo['paid_tick']))/3600>1 else 0,
				})
			result['num']=len(result['data'])

		#print result
		web.header("Content-Type", "application/json")
		return json.dumps(result)

