#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/wxpay')

wx_appid='wx287354be40913e99'
wx_appsecret='86f63620d4c502d4d5ac7bb5483f600d'
mch_id='1260745901'
api_key='0378881f16430cf597cc1617be53db37'
#notify_url='http://app-test.urfresh.cn:12048/app/wxpay_notify'
notify_url='http://%s:12048/app/wxpay_notify' % setting.app_host

# 获取微信支付id
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', order_id='', total='', sign='')

		if '' in (param.app_id, param.order_id, param.session, param.total, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if web.ctx.has_key('environ'):
			client_ip = web.ctx.environ['REMOTE_ADDR']
		else:
			return json.dumps({'ret' : -5, 'msg' : '无法取得客户端ip地址'})

		uname = app_helper.logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.order_id, param.total])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})


			# 统一下单接口获取 prepay_id
			nonce_str = app_helper.my_rand(30)
			body = 'U掌柜app'
			trade_type = 'APP'
			order_id = param.order_id.encode('utf-8')
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
				return json.dumps({'ret' : 0, 'data' : data})
			else:
				return json.dumps({'ret' : -1, 'data' : r.status})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
