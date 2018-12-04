#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper
from order_checkout import checkout

db = setting.db_web

url = ('/app/(v2|v3)/wxpay')

wx_appid='wx287354be40913e99'
wx_appsecret='86f63620d4c502d4d5ac7bb5483f600d'
mch_id='1260745901'
api_key='0378881f16430cf597cc1617be53db37'
#notify_url='http://app-test.urfresh.cn:12048/app/wxpay_notify'
notify_url='http://%s:12048/app/wxpay_notify' % setting.notify_host

# 获取微信支付id
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', order_id='', total='', note='', sign='')

		if version=='v2':
			if '' in (param.app_id, param.order_id, param.session, param.total, param.sign):
				return json.dumps({'ret' : -2, 'msg' : '参数错误'})
		elif version=='v3':
			if '' in (param.app_id, param.session, param.total, param.sign):
				return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if web.ctx.has_key('environ'):
			client_ip = web.ctx.environ['REMOTE_ADDR']
		else:
			return json.dumps({'ret' : -5, 'msg' : '无法取得客户端ip地址'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id, param.total, param.note])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			#db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})


			# 统一下单接口获取 prepay_id
			nonce_str = app_helper.my_rand(30)
			body = 'U掌柜app'
			trade_type = 'APP'

			if version=='v2':
				order_id = '%s_%d' % (param.order_id.encode('utf-8'), int(time.time()))
			elif version=='v3':
				if len(param.order_id)>0:
					order_id = '%s_%d' % (param.order_id.encode('utf-8'), int(time.time()))
					print order_id
				else:
					# 生成order_id
					order_id = app_helper.get_new_order_id(version).encode('utf-8')
					print 'new order_id', order_id

			total_fee = param.total.encode('utf-8')
			para = [
				('appid'            , wx_appid),
				('body'             , body),
				('mch_id'           , mch_id),
				('nonce_str'        , nonce_str),
				('notify_url'       , notify_url),
				('out_trade_no'     , order_id),
				('spbill_create_ip' , client_ip),
				('total_fee'        , total_fee),
				('trade_type'       , trade_type)
			]

			print para

			stringA = '&'.join('%s=%s' % i for i in para)
			stringSignTemp = '%s&key=%s' % (stringA, api_key)
			sign = hashlib.md5(stringSignTemp).hexdigest().upper()

			para_xml = '<xml>' \
				'<appid>'+wx_appid+'</appid>' \
				'<mch_id>'+mch_id+'</mch_id>' \
				'<nonce_str>'+nonce_str+'</nonce_str>' \
				'<sign>'+sign+'</sign>' \
				'<body>'+body+'</body>' \
				'<out_trade_no>'+order_id+'</out_trade_no>' \
				'<total_fee>'+total_fee+'</total_fee>' \
				'<spbill_create_ip>'+client_ip+'</spbill_create_ip>' \
				'<notify_url>'+notify_url+'</notify_url>' \
				'<trade_type>'+trade_type+'</trade_type>' \
				'</xml>'

			print para_xml
			#return json.dumps({'ret' : 0, 'data' : 'here'})

			urllib3.disable_warnings()
			pool = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
			url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
			r = pool.urlopen('POST', url, body=para_xml)
			if r.status==200:
				data = r.data
				print data
				if version=='v2':
					# 记录微信商户订单号
					db.order_app.update_one({'order_id':param.order_id},{'$set':{'wx_out_trade_no':order_id}})
					return json.dumps({'ret' : 0, 'data' : data})
				elif version=='v3':
					if len(param.order_id)>0:
						db_order = db.order_app.find_one({'order_id':param.order_id})
						if db_order['status']!='DUE':
							print '============================== -100'
							return json.dumps({'ret' : -100, 'msg' : '订单状态变化，请确认'})
						ret_json = checkout(version, uname, {
							'session'   : param.session,
							'order_id'  : param.order_id,
							'shop_id'   : str(db_order['shop']),
							'addr_id'   : db_order['address'][0],
							'coupon_id' : db_order['coupon'][0] if float(db_order['coupon_disc'])>0 else '',
							'cart'      : json.dumps(db_order['cart']),
							'app_id'    : param.app_id,
							'use_credit': '1' if float(db_order.get('use_credit','0'))>0 else '', #2015-11-19
						})
						if ret_json['ret']<0:
							# checkout 出错
							return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

						if float(ret_json['data']['due'])!=float(db_order.get('due3', db_order['due'])):
							# checkout后金额有变化，说明库存或优惠券有变化
							db.order_app.update_one({'order_id':param.order_id},{
								'$set'  : {'status': 'CANCEL'},
								'$push' : {'history':(app_helper.time_str(), uname['uname'], '订单取消(微信支付)')}
							})
							print '============================== -100'
							return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，订单已取消，请重新下单'})

						# 可支付

						db.order_app.update_one({'order_id':param.order_id},{
							'$set'  : {'wx_out_trade_no':order_id},
							'$push' : {'history':(app_helper.time_str(), uname['uname'], '提交微信支付2')}
						})
						return json.dumps({'ret' : 0, 'order_id' : param.order_id, 'data' : data})
					else:
						# 生成新订单
						db_cart = db.app_user.find_one({'uname':uname['uname']},{'cart_order.%s'%param.session:1})
						new_order = dict(db_cart['cart_order'][param.session])
						new_order['order_id']=order_id
						new_order['status']='DUE'
						new_order['user_note']=param.note.strip()
						new_order['wx_out_trade_no']=order_id
						new_order['history']=[(app_helper.time_str(), uname['uname'], '提交微信支付')]

						ret_json = checkout(version, uname, {
							'session'   : param.session,
							'order_id'  : order_id,
							'shop_id'   : str(new_order['shop']),
							'addr_id'   : new_order['address'][0],
							'coupon_id' : new_order['coupon'][0] if float(new_order['coupon_disc'])>0 else '',
							'cart'      : json.dumps(new_order['cart']),
							'app_id'    : param.app_id,
							'use_credit': '1' if float(new_order.get('use_credit','0'))>0 else '', #2015-11-23
						})

						if ret_json['ret']<0:
							# checkout 出错
							return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

						if float(ret_json['data']['due'])!=float(new_order.get('due3', new_order['due'])):
							# checkout后金额有变化，说明库存或优惠券有变化
							print '============================== -100'
							return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单'})

						db.order_app.insert_one(new_order)
						return json.dumps({'ret' : 0, 'order_id' : order_id, 'data' : data})
			else:
				return json.dumps({'ret' : -1, 'data' : r.status})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
