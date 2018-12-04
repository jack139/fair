#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, helper

db = setting.db_web

url = ('/app/(v2|v3)/order_detail')

# 取消订单
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', order_id='', sign='')

		if '' in (param.app_id, param.session, param.order_id, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_user = db.app_user.find_one({'uname':uname['uname']},{'coupon':1, 'credit':1})
			if db_user==None: # 不应该发生
				return json.dumps({'ret' : -5, 'msg' : '未找到用户信息'})

			# 修改为付款的过期订单
			r = db.order_app.update_many({
				'uname'    : {'$in':uname.values()},
				'status'   : 'DUE',
				'deadline' : {'$lt':int(time.time())}
			}, {'$set': {'status':'TIMEOUT'}})

			# 获得订单
			#print param.order_id, uname
			db_order = db.order_app.find_one({'order_id' : param.order_id, 'user':{'$in':uname.values()}})
			if db_order==None:
				return json.dumps({'ret' : -3, 'msg' : '未找到订单！'})

			cart=[]
			for i in db_order['cart']:
				r = db.sku_store.find_one({'product_id':i['product_id']},
					{'base_sku':1})
				base_sku = db.dereference(r['base_sku'])
				image = base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else ''
				cart.append({
					'product_id' : i['product_id'],
					'title'      : i['title'],
					'price'      : i['price'],
					'num2'       : i['num2'],
					'numyy'      : i.get('numyy',0), # v3 使用
					'image'      : '/%s/%s' % (image[:2], image),
				})

			data={
				'order_id'     : db_order['order_id'],
				'shop'         : str(db_order['shop']), # 需要中文名
				'status'       : helper.ORDER_STATUS['APP'].get(db_order['status'],'未知状态'),  # 需要中文名
				'deadline'     : db_order['deadline']-int(time.time()), # 离支付截至的时间,秒数
				'delivery'     : {
					'address'     : db_order['address'][3],
					'contact'     : db_order['address'][1],
					'contact_tel' : db_order['address'][2],
					'runner'      : db_order['runner']['name'] if db_order.has_key('runner') else '', # 送货员姓名
					'runner_tel'  : db_order['runner']['tel'] if db_order.has_key('runner') else '', # 送货员电话
				}, 
				'cart'         : cart,
				'total'        : db_order['total'],
				'coupon'       : db_order['coupon'][0] if db_order['coupon'] else '',
				'coupon_disc'  : db_order['coupon_disc'],
				'first_disc'   : db_order['first_disc'],
				'delivery_fee' : db_order['delivery_fee'],
				'due'          : db_order['due'],
				'star'         : db_order.get('star', 1),
				'credit'       : '%.2f' % db_user.get('credit', 0.0),
			}
			if version=='v3':
				data['use_credit']= db_order.get('use_credit', '0.00') # 余额支付的金额
				data['due3']= db_order.get('due3', db_order['due']) # 第3方支付的金额
				data['history']=[] # 返回订单历史
				for i in db_order['history']:
					if 'COMPLETE' in i[2]:
						action = '订单完成'
					elif i[2].encode('utf-8')=='提交结算':
						continue
					elif 'PAID' in i[2] or i[2].encode('utf-8')=='付款通知':
						action = '已付款'
					elif 'REFUND' in i[2]:
						action = '有退款'
					elif 'CANCEL' in i[2]:
						action = '订单已取消'
					elif 'FAIL' in i[2]:
						action = '配送失败'
					elif 'DISPATCH' in i[2]:
						action = '开始拣货'
					else:
						action = i[2]
					data['history'].append({
						'time'   : i[0],
						'action' : action,
					})
				pay_type = db_order.get('pay_type')
				if pay_type=='CREDIT':
					data['pay_type']='余额支付'
				elif pay_type=='ALIPAY':
					data['pay_type']='支付宝'
				elif pay_type=='WXPAY':
					data['pay_type']='微信支付'
				else:
					data['pay_type']='n/a'

			print data

			return json.dumps({'ret' : 0, 'data' : data})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
