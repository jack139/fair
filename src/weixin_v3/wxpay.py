#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper
from pt_order_checkout import pt_checkout
from order_checkout import checkout

db = setting.db_web

url = ('/wx/wxpay')

# U掌柜 设置
#wx_appid='wx2527355bfd909dbe' # 公众号
#wx_appsecret='49e8eb83c3fce102215a92047e8e9290' # 公众号
#mch_id='1253845801'

# F8KAM 设置 － 测试
#wx_appid='wxb920ef74b6a20e69' # 公众号
#wx_appsecret='ddace9d14b3413c65991278f09a03896' # 公众号
#mch_id='1242104702'

wx_appid=setting.wx_setting['wx_appid']
wx_secret=setting.wx_setting['wx_appsecret']
mch_id=setting.wx_setting['mch_id']

api_key='0378881f16430cf597cc1617be53db37'
notify_url='http://%s:12048/app/wxpay_notify' % setting.app_host


# 获取微信支付id
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', pt_order_id='', order_id='', type='', total='')

		print param

		if '' in (param.total, param.type):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if web.ctx.has_key('environ'):
			client_ip = web.ctx.environ['REMOTE_ADDR']
		else:
			return json.dumps({'ret' : -5, 'msg' : '无法取得客户端ip地址'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

			db_session = db.app_sessions.find_one({'session_id':param.session_id},{'ticket':1}) 
			ticket = db_session.get('ticket','')

			# 修改为付款的过期订单
			r = db.order_app.update_many({
				'uname'    : {'$in' : uname.values()},
				'status'   : 'DUE',
				'deadline' : {'$lt':int(time.time())}
			}, {'$set': {'status':'TIMEOUT'}})

			# 统一下单接口获取 prepay_id
			nonce_str = app_helper.my_rand(30)
			body = 'U掌柜app'
			trade_type = 'JSAPI'
			if len(param.order_id)>0:
				#order_id = '%s_%d' % (param.order_id.encode('utf-8'), int(time.time()))
				order_id = param.order_id.encode('utf-8')
			else:
				# 生成order_id, 2015-10-29
				order_id = app_helper.get_new_order_id('x').encode('utf-8')
				# 拼团订单 t 开头
				if param.type=='TUAN':
					order_id = 't'+order_id[1:]
			total_fee = param.total.encode('utf-8')
			openid = uname['openid'].encode('utf-8')
			para = [
				('appid'            , wx_appid),
				('body'             , body),
				('mch_id'           , mch_id),
				('nonce_str'        , nonce_str),
				('notify_url'       , notify_url),
				('openid'           , openid),
				('out_trade_no'     , order_id),
				('spbill_create_ip' , client_ip),
				('total_fee'        , total_fee),
				('trade_type'       , trade_type)
			]

			#print para

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
				'<openid>'+openid+'</openid>' \
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
				# 检查和生成订单
				if len(param.order_id)>0:
					db_order = db.order_app.find_one({'order_id':param.order_id})
					if db_order['status']!='DUE':
						print '============================== -100'
						return json.dumps({'ret' : -100, 'msg' : '订单状态变化，请确认'})

					# 再次 checkout
					if param.type=='TUAN':
						ret_json = pt_checkout( uname, {
							'region_id'   : db_order['region_id'],
							'addr_id'     : db_order['address'][0],
							'coupon_id'   : db_order['coupon'][0] if float(db_order['coupon_disc'])>0 else '',
							'cart'        : json.dumps(db_order['cart']),
							'pt_order_id' : db_order['pt_order_id'],
						})
						if ret_json['ret']<0:
							# checkout 出错
							return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})
					else:
						ret_json = checkout( uname, {
							'shop_id'     : str(db_order['shop']),
							'addr_id'     : db_order['address'][0],
							'coupon_id'   : db_order['coupon'][0] if float(db_order['coupon_disc'])>0 else '',
							'cart'        : json.dumps(db_order['cart']),
							'order_id'    : db_order['order_id'],
						})
						if ret_json['ret']<0:
							# checkout 出错
							return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

						if float(ret_json['data']['due'])!=float(db_order['due']):
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
						'$push' : {'history':(app_helper.time_str(), uname['openid'], '提交微信支付2')}
					})
					if param.type=='TUAN':
						# 拼团订单
						return json.dumps({
							'ret'         : 0, 
							'order_id'    : param.order_id, 
							'pt_order_id' : db_order['pt_order_id'],
							'position'    : db_order['position'], 
							'data'        : data, 
							'ticket'      : ticket
						})
					else:
						# 1小时订单
						return json.dumps({
							'ret'      : 0, 
							'order_id' : param.order_id, 
							'data'     : data, 
							'ticket'   : ticket
						})
				else:
					# 生成新订单
					db_cart = db.app_user.find_one({'openid':uname['openid']},{'cart_order_wx':1})
					if param.type=='TUAN':
						# 拼团订单
						if not db_cart.has_key('cart_order_wx'):
							print 'fail: 不该发生, 缺少购物车数据'
							return json.dumps({'ret' : -9, 'msg' : '系统错误，请重试！'})

						new_order = dict(db_cart['cart_order_wx'][0])
						new_order['order_id']=order_id
						new_order['status']='DUE'
						new_order['user_note']=param.note.strip()
						new_order['wx_out_trade_no']=order_id
						new_order['history']=[(app_helper.time_str(), uname['openid'], '提交微信支付')]

						# 如果是新开团，添加pt_order
						if len(db_cart['cart_order_wx'])>1:
							new_pt_order = dict(db_cart['cart_order_wx'][1])
							new_pt_order['pt_order_id']='pt'+order_id[1:]
							new_pt_order['status']='WAIT'
							new_pt_order['history']=[(app_helper.time_str(), uname['openid'], '等待开团')]
							db.pt_order.insert_one(new_pt_order)
							# 订单数据里添加 pt_order_id
							new_order['pt_order_id']=new_pt_order['pt_order_id']

						# 再次 checkout
						ret_json = pt_checkout( uname, {
							'region_id'   : new_order['region_id'],
							'addr_id'     : new_order['address'][0],
							'coupon_id'   : new_order['coupon'][0] if float(new_order['coupon_disc'])>0 else '',
							'cart'        : json.dumps(new_order['cart']),
							'pt_order_id' : new_order['pt_order_id'],
						})
						if ret_json['ret']<0:
							print 'checkout 检查未通过，不能支付'
							return json.dumps({'ret' : -9, 'msg' : ret_json['msg']})

						db.order_app.insert_one(new_order)
						return json.dumps({
							'ret'         : 0, 
							'order_id'    : new_order['order_id'], 
							'pt_order_id' : new_order['pt_order_id'],
							'position'    : new_order['position'], # 测试
							'data'        : data, 
							'ticket'      : ticket
						})

					else:
						# 1小时订单
						new_order = dict(db_cart['cart_order_wx'])
						new_order['order_id']=order_id
						new_order['status']='DUE'
						new_order['user_note']=param.note.strip()
						new_order['wx_out_trade_no']=order_id
						new_order['history']=[(app_helper.time_str(), uname['openid'], '提交微信支付')]

						# 再次 checkout
						ret_json = checkout( uname, {
							'shop_id'     : str(new_order['shop']),
							'addr_id'     : new_order['address'][0],
							'coupon_id'   : new_order['coupon'][0] if float(new_order['coupon_disc'])>0 else '',
							'cart'        : json.dumps(new_order['cart']),
							'order_id'    : new_order['order_id'],
						})
						if ret_json['ret']<0:
							print 'checkout 检查未通过，不能支付'
							return json.dumps({'ret' : -9, 'msg' : ret_json['msg']})

						if float(ret_json['data']['due'])!=float(new_order['due']):
							# checkout后金额有变化，说明库存或优惠券有变化
							print '============================== -100'
							return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单'})

						db.order_app.insert_one(new_order)
						return json.dumps({
							'ret'         : 0, 
							'order_id'    : order_id, 
							'data'        : data, 
							'ticket'      : ticket
						})
			else:
				return json.dumps({'ret' : -1, 'data' : r.status})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
