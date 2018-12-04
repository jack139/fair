#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, gc
import time, json, hashlib, random
import rsa, base64
from bson.objectid import ObjectId
from config.url_api import urls
from config import setting
import app_helper #, jpush
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET


db = setting.db_web  # 默认db使用web本地

app = web.application(urls, globals())
application = app.wsgifunc()

#----------------------------------------

gc.set_threshold(300,5,5)

###########################################

def my_crypt(codestr):
	return hashlib.sha1("sAlT139-"+codestr).hexdigest()

def my_rand(n=8):
	return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for ch in range(n)])

########### APP接口 #######################################################

## 需优化内容：
# 1. 出错info页面要做微信端优化 --> 直接跳转回init页面
# 2. urlopen, json.loads 需要处理异常！


# 常量
public_key='DDACE9D14B3413C65991278F09A03896'
public_key_v2='DHTTG9D14B3413C65991278F09A03896'


##### 核对签名  =======================================================

def quick(L):
	if len(L) <= 1: return L
	return quick([a for a in L[1:] if a[0] < L[0][0]]) + L[0:1] + quick([b for b in L[1:] if b[0] >= L[0][0]])

def check_sign_wx(str_xml):
	api_key='0378881f16430cf597cc1617be53db37'

	xml=ET.fromstring(str_xml)
	params = []
	sign0 = None
	for i in xml:
		if i.tag=='sign':
			sign0 = i.text
			continue
		params.append((i.tag, i.text))

	param2 = quick(params)
	stringA = '&'.join('%s=%s' % (i[0],i[1]) for i in param2)
	stringSignTemp = '%s&key=%s' % (stringA, api_key)
	sign = hashlib.md5(stringSignTemp).hexdigest().upper()
	return (sign0==sign)

RSA_PUBLIC = "-----BEGIN PUBLIC KEY-----\n" \
	"MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRA\n" \
	"FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQE\n" \
	"B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ksi\n" \
	"NG9zpgmLCUYuLkxpLQIDAQAB\n" \
	"-----END PUBLIC KEY-----"

def check_sign_alipay(ret):
	params = []
	sign0 = None
	for i in ret.keys():
		if i=='sign_type':
			continue
		elif i=='sign':
			sign0 = ret[i]
			continue
		params.append((i, ret[i]))

	param2 = quick(params)
	stringA = '&'.join('%s=%s' % (i[0],i[1]) for i in param2)
	_public_rsa_key_ali = rsa.PublicKey.load_pkcs1_openssl_pem(RSA_PUBLIC)
	sign = base64.decodestring(sign0)
	try:
		rsa.verify(stringA.encode('utf-8'), sign, _public_rsa_key_ali)
		return True
	except Exception,e:
		print "check_sign_alipay error: ", e
		return False

##### ==================================================================

# 首次握手
class FisrtHand:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		param=web.input(type='', secret='', sign='')

		if '' in (param.type, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.type not in ['IOS', 'ANDROID']:
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		sign_str = '%s%s%s' % (public_key, param.type, param.secret)
		md5_str = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 注册新app
		app_id = my_rand().upper()
		if db.app_device.find({'app_id' : app_id}).count()>0:
			# 两次随机仍重复的可能性，很小吧
			app_id = my_rand().upper()
		private_key = my_crypt(app_id).upper()
		db.app_device.insert_one({
			'app_id'      : app_id, 
			'private_key' : private_key, 
			'type'        : param.type
		})

		return json.dumps({'ret' : 0, 'data' : {
			'app_id'      : app_id,
			'private_key' : private_key,
		}})

# 首次握手 v2，公钥不同
class FisrtHand_v2:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		param=web.input(type='', secret='', sign='')

		print web.data()

		if '' in (param.type, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.type not in ['IOS', 'ANDROID']:
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		sign_str = '%s%s%s' % (public_key_v2, param.type, param.secret)
		md5_str = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 注册新app
		app_id = my_rand().upper()
		if db.app_device.find({'app_id' : app_id}).count()>0:
			# 两次随机仍重复的可能性，很小吧
			app_id = my_rand().upper()
		private_key = my_crypt(app_id).upper()
		db.app_device.insert_one({
			'app_id'      : app_id, 
			'private_key' : private_key, 
			'type'        : param.type
		})

		return json.dumps({'ret' : 0, 'data' : {
			'app_id'      : app_id,
			'private_key' : private_key,
		}})

# 取得主机端口
class GetHost:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', secret='', sign='')

		if '' in (param.app_id, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 返回host地址、端口
		host = setting.app_pool[random.randint(0,len(setting.app_pool)-1)]
		print 'host = ', host
		return json.dumps({'ret' : 0, 'data' : {
			'protocol' : 'http',
			#'host'     : setting.app_host, #'app.urfresh.cn',
			'host'     : host,
			'port'     : '12050',
		}})

# 阿里云异步通知
# {	'seller_email': u'pay@urfresh.cn', 
#	'refund_status': u'REFUND_SUCCESS', 
#	'trade_status': u'TRADE_CLOSED', 
#	'gmt_close': u'2015-07-26 22:10:10', 
# 	'sign': u'GuNPbLf5+qEtGbcgroLtbocHEuA7srFhj12lBCTg2ZC/mbi08GtcB0loQx5K4DS2KLbKhkBOtQZf4u1Nhln9G03SjBpQZwz11xyQNXjBvKNkk3jfiE6T5KGtWpp8Y4sCQXySoYjh6M70JKajyHwupxGvBxcxcRPSRUp14J2SXP8=', 
#	'gmt_refund': u'2015-07-26 22:10:10', 'subject': u'U\u638c\u67dc', 'is_total_fee_adjust': u'N', 
#	'gmt_create': u'2015-07-26 21:55:41', 'out_trade_no': u'n000148', 'sign_type': u'RSA', 
#	'body': u'n000148', 'price': u'1.00', 'buyer_email': u'1010694499@qq.com', 'discount': u'0.00', 
#	'gmt_payment': u'2015-07-26 21:55:42', 
#	'trade_no': u'2015072600001000290059171016', 'seller_id': u'2088021137384128', 
#	'use_coupon': u'N', 'payment_type': u'1', 'total_fee': u'1.00', 'notify_time': u'2015-07-26 22:10:11', 
#	'quantity': u'1', 'notify_id': u'45a440807ef37f807132a25e8445844d3m', 
#	'notify_type': u'trade_status_sync', 'buyer_id': u'2088502264376292'	}
class AlipayNotify:
	def POST(self, version='v1'):
		param = web.input()
		print param

		if check_sign_alipay(param):
			print "ALIPAY SIGNATURE CHECK SUCCESS!"
		else:
			print "ALIPAY SIGNATURE CHECK FAIL ......!"
			return 'fail'

		order_id = param.get('out_trade_no','')
		if param.get('refund_status') == 'REFUND_SUCCESS': # 有退款
			db.order_app.update_one({'order_id':order_id},{
				'$set'  : {
					'status'      : 'REFUND',
					'refund_time' : param.get('gmt_refund'),
					'refund_tick' : int(time.time()),
				},
				'$push' : {
					'ali_notify': param,
					'history'   : (app_helper.time_str(), 'alipy', '退款通知')
				}
			})
		elif param.get('trade_status') == 'TRADE_SUCCESS': # 有付款
			r = db.order_app.find_one({'order_id':order_id},
				#{'due':1, 'uname':1, 'coupon':1, 'shop':1, 'cart':1, 'status':1})
				{'_id':0})
			if r:
				status = 'PAID'
				
				#if float(r['due'])<=float(param.get('total_fee','0')): # 检查支付金额与应付是否一致
				#	status = 'PAID'
				#else:
				#	status = 'PARTIAL_PAID'

				print r['status']

				db_user = db.app_user.find_one({'$or' : [ 
					{'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
				]})

				if r['status'] in ['DUE', 'PREPAID', 'TIMEOUT']: # 如果状态已是PAID，说明有重复通知，不减库存
					# 消费余额
					if float(r.get('use_credit', '0'))>0:
						print db_user['credit'],float(r['use_credit'])
						if db_user['credit']>=float(r['use_credit']): # 余额够用
							db.app_user.update_one({'$or' : [ 
									{'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
								]},{
								'$inc' : { 
									'credit' : 0-float(r['use_credit']), 
								},
								'$push' : { 
									'credit_history' : (  # 专门记录余额消费
										app_helper.time_str(), 
										'消费余额',
										'-%.2f' % float(r['use_credit']),
										'订单: %s' % order_id.encode('utf-8')
									)
								},
							})
						else: # 余额不够用

							# 修改订单状态
							db.order_app.update_one({'order_id':order_id},{
								'$set'  : {
									'status'       : 'CANCEL_TO_REFUND',
									#'sum_to_refund' : r['due'], # 没有 sum_to_refund 表示全额退
									'use_credit'    : '0.00', # 清除余额支付，防止多退款
									'use_credit_old': r['use_credit'], # 保存应收余额支付金额
									#'cart'         : b2,     # 更新购物车  2015-09-11
									'ali_trade_no' : param.get('trade_no'),
									'paid_time'    : param.get('gmt_payment'),
									'paid_tick'    : int(time.time()),
									'pay_type'     : 'ALIPAY',
								},
								'$push' : {
									'ali_notify': param,
									'history'   : (app_helper.time_str(), 'alipay', '付款通知:余额不足转入退款')
								}
							})

							return 'success'


					# 使用的优惠券失效

					coupon = []
					if r['coupon']!=None:
						for i in db_user['coupon']:
							if i[0]==r['coupon'][0]: # 这次使用
								i2=list(i)
								i2[3]=0
								coupon.append(i2)
							else:
								coupon.append(i)
					else:
						coupon = db_user['coupon']
					# 满30送5元抵用券
					#if float(param.get('total_fee','0'))>=30:
					#	valid = app_helper.time_str(time.time()+3600*24*30, 1)
					#	coupon.append((app_helper.my_rand(), valid, '5.00', 1))
					# 首单送抵用券
					#if db.order_app.find({'user':r['uname'],'status':{'$nin':['TIMEOUT','DUE','CANCEL']},'order_id':{'$ne':order_id}},{'_id':1}).count()==0:
					#	# (id, 有效期, 金额, 是否已用, 门槛) 2015-09-27
					#	valid = app_helper.time_str(time.time()+3600*24*30, 1)
					#	if str(r['shop']) in app_helper.new_coupon2_shop:
					#		print '首单送优惠券(指定店)'							
					#		for i in app_helper.new_coupon2:
					#			coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
					#	else:
					#		print '首单送优惠券'							
					#		for i in app_helper.new_coupon:
					#			coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
					# 更新优惠券
					db.app_user.update_one({'uname':r['uname']}, {'$set':{'coupon':coupon}})

					# 邀请码用户送抵用券 2015-10-24
					invitation = db_user.get('invitation', '')
					if invitation!='' and db_user.get('invite_coupon_has_sent', 0)==0: # 已填邀请码并且未送过券
						coupon_user = db.app_user.find_one({'my_invit_code':invitation},{'uname':1})
						if coupon_user:
							# 送邀请码用户抵用券
							print '送邀请码用户抵用券'
							valid = app_helper.time_str(time.time()+3600*24*30, 1)
							db.app_user.update_one({'uname':coupon_user['uname']},{'$push':{
								'coupon' : (app_helper.my_rand(), valid, '5.00', 1, 19.9, 'apple')
							}})
							# 设置已送标志
							db.app_user.update_one({'uname':r['uname']}, {'$set':{'invite_coupon_has_sent':1}})


					# 正常减库存！
					# item = [ product_id, num, num2, price]
					# k - num 库存数量
					print "修改库存."

					b2 = [] # C端商品
					b3 = [] # B3整箱预售商品
					b3_total = 0.0
					for item in r['cart']:
						# 记录销售量
						db.sku_store.update_one({'product_id' : item['product_id']},
							{'$inc' : {'volume' : float(item['num2'])}}
						)

						# 暂停整箱预售 2015-10-27
						#r3 = db.sku_store.find_one({'product_id' : item['product_id']},
						#	{'list_in_app':1})
						#if r3['list_in_app']==3: # B3商品不需要改库存
						#	b3_total += float(item['price'])
						#	b3.append(item)
						#	item['title'] = item['title']+u'（整箱预售，次日送达）'
						#	b2.append(item)
						#	continue

						# 买一送一
						if item.has_key('numyy'): # v3 2015-10-25
							if item['product_id'] in app_helper.buy_X_give_Y.keys():
								print '买X送Y'
								#item['num2'] = int(float(item['num2']) + float(item['numyy']))
								#item['title'] = item['title'] + u'特惠活动'
						else:
							if item['product_id'] in app_helper.buy_1_give_1:
								print '买一送一'
								lc_num2 = float(item['num2'])
								item['num2'] = int(lc_num2 + lc_num2)
								item['title'] = item['title'].replace(u'买一送一',u'特惠活动')

						# 过滤数量价格为零的
						if item['num2']==0 and float(item['price'])==0.0:
							continue

						# num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
						num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
						r2 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
							{
								'product_id' : item['product_id'],
								'shop'       : r['shop'],
							},
							{ 
								'$inc'  : { 
									'num'         : 0-num_to_change, 
								 	'pre_pay_num' : num_to_change, # 记录预付数量
								}
								#'$push' : { 'history' : (helper.time_str(), 
								#	helper.get_session_uname(), '售出 %s' % str(item['num']))},
							},
							{'_id':1}
						)
						#print r
						if r2==None: # 不应该发生
							return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
						else:
							b2.append(item)
						
						# 更新第3方库存 2015-10-10
						app_helper.elm_modify_num(r['shop'], item['product_id'])

					# 检查是否有b3商品, 3种情况
					# 1. b2, b3 都有，拆单
					# 2. 只有b3，站点改为B3站点，保留收货站点
					# 3. 只有b2，保持订单不变
					#print b2
					#print b3
					if len(b3)>0 and (len(b2)-len(b3))>0: # 情况1
						print "拆单"
						r4 = r.copy()
						r4['order_id']     = r4['order_id']+u'-b3'
						r4['shop_0']       = r['shop']
						r4['shop']         = ObjectId(setting.B3_shop)
						r4['cart']         = b3
						r4['status']       = status
						r4['ali_trade_no'] = param.get('trade_no')
						r4['paid_time']    = param.get('gmt_payment')
						r4['paid_tick']    = int(time.time())
						r4['history']      = [(app_helper.time_str(), 'alipay', '付款通知－拆单')]
						r4['total']        = '%.2f' % b3_total
						r4['cost']         = '0.00'
						r4['coupon_disc']  = '0.00'
						r4['first_disc']   = '0.00'
						r4['delivery_fee'] = '0.00'
						r4['due']          = '0.00'
						db.order_app.insert_one(r4) # 增加子订单
					elif len(b3)>0: # 情况 2
						print "订单改到B3站点"
						# 如果订单地址不再配送范围，则由b3直接发出， 2015-10-18
						if r.get('poly_shop', 1)==1: # 默认到店配送
							print 'b3配送到店'
							shop_0 = r['shop']
						else:
							print 'b3直接发货'
							shop_0 = ObjectId(setting.B3_shop)
						db.order_app.update_one({'order_id':order_id},{'$set' : {
							'shop_0' : shop_0,
							'shop'   : ObjectId(setting.B3_shop),
						}})
					else: # 情况3，什么都不做
						print "订单保持不变"

					# 推送通知
					#if len(r['uname'])==11 and r['uname'][0]=='1':
					#	jpush.jpush('已收到您的付款，我们会尽快处理。', r['uname'])
				else:
					print "重复通知：alipay"
					b2 = r['cart']


				# 修改订单状态
				db.order_app.update_one({'order_id':order_id},{
					'$set'  : {
						'status'       : status,
						'cart'         : b2,     # 更新购物车  2015-09-11
						'ali_trade_no' : param.get('trade_no'),
						'paid_time'    : param.get('gmt_payment'),
						'paid_tick'    : int(time.time()),
						'pay_type'     : 'ALIPAY',
						'credit_total' : '%.2f' % float(r.get('use_credit', '0')),
						'alipay_total' : param.get('total_fee','0.00'), # 支付宝实际支付
					},
					'$push' : {
						'ali_notify': param,
						'history'   : (app_helper.time_str(), 'alipay', '付款通知')
					}
				})

		return 'success'


# 微信支付异步通知
#<xml>
#  <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
#  <attach><![CDATA[支付测试]]></attach>
#  <bank_type><![CDATA[CFT]]></bank_type>
#  <fee_type><![CDATA[CNY]]></fee_type>
#  <is_subscribe><![CDATA[Y]]></is_subscribe>
#  <mch_id><![CDATA[10000100]]></mch_id>
#  <nonce_str><![CDATA[5d2b6c2a8db53831f7eda20af46e531c]]></nonce_str>
#  <openid><![CDATA[oUpF8uMEb4qRXf22hE3X68TekukE]]></openid>
#  <out_trade_no><![CDATA[1409811653]]></out_trade_no>
#  <result_code><![CDATA[SUCCESS]]></result_code>
#  <return_code><![CDATA[SUCCESS]]></return_code>
#  <sign><![CDATA[B552ED6B279343CB493C5DD0D78AB241]]></sign>
#  <sub_mch_id><![CDATA[10000100]]></sub_mch_id>
#  <time_end><![CDATA[20140903131540]]></time_end>
#  <total_fee>1</total_fee>
#  <trade_type><![CDATA[JSAPI]]></trade_type>
#  <transaction_id><![CDATA[1004400740201409030005092168]]></transaction_id>
#</xml>
class WxpayNotify:
	def POST(self, version='v1'):
		param = web.input()
		print param

		str_xml=web.data()
		print str_xml

		if check_sign_wx(str_xml):
			print "WXPAY SIGNATURE CHECK SUCCESS!"
		else:
			print "WXPAY SIGNATURE CHECK FAIL ......!"
			return 	'<xml>' \
	  			'<return_code><![CDATA[FAIL]]></return_code>' \
	  			'<return_msg><![CDATA[签名失败]]></return_msg>' \
				'</xml>' 

		xml=ET.fromstring(str_xml)
		return_code = xml.find('return_code').text
		if return_code!='SUCCESS':  # 通信失败
			return 	'<xml>' \
	  			'<return_code><![CDATA[FAIL]]></return_code>' \
	  			'<return_msg><![CDATA[FAIL]]></return_msg>' \
				'</xml>' 

		result_code = xml.find('result_code').text
		if result_code=='SUCCESS': # 有付款
			# v2 开始微信支付out_trade_no，在order_id后加时间戳 2015-09-19
			order_id0 = xml.find('out_trade_no').text
			order_id = order_id0.split('_')[0]

			r = db.order_app.find_one({'order_id':order_id},
				#{'due':1, 'uname':1, 'coupon':1, 'shop':1, 'cart':1, 'status':1})
				{'_id':0})
			if r:
				status = 'PAID'

				comment = '' # 用于记录history时附加信息 2015-11-21

				#if float(r['due'])<=float(xml.find('total_fee').text): # 检查支付金额与应付是否一致
				#	status = 'PAID'
				#else:
				#	status = 'PARTIAL_PAID'

				print r['status']

				db_user = db.app_user.find_one({'$or' : [ 
					{'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
				]})

				if r['status'] in ['DUE', 'PREPAID', 'TIMEOUT']: # 如果状态已是PAID，说明有重复通知，不减库存

					# 消费余额
					if float(r.get('use_credit', '0'))>0:
						print db_user['credit'],float(r['use_credit'])
						if db_user['credit']>=float(r['use_credit']): # 余额够用
							db.app_user.update_one({'$or' : [ 
									{'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
								]},{
								'$inc' : { 
									'credit' : 0-float(r['use_credit']), 
								},
								'$push' : { 
									'credit_history' : (  # 专门记录余额消费
										app_helper.time_str(), 
										'消费余额',
										'-%.2f' % float(r['use_credit']),
										'订单: %s' % order_id.encode('utf-8')
									)
								},
							})
						else: # 余额不够用

							# 修改订单状态
							t = xml.find('time_end').text
							paid_time = '%s-%s-%s %s:%s:%s' % (t[:4],t[4:6],t[6:8],t[8:10],t[10:12],t[12:])
							db.order_app.update_one({'order_id':order_id},{
								'$set'  : {
									'status'       : 'CANCEL_TO_REFUND',
									#'sum_to_refund' : r['due'],
									'use_credit'    : '0.00', # 清除余额支付，防止多退款
									'use_credit_old': r['use_credit'], # 保存应收余额支付金额
									#'cart'         : b2,     # 更新购物车  2015-09-11
									'wx_trade_no'  : xml.find('transaction_id').text,
									'paid_time'    : paid_time,
									'paid_tick'    : int(time.time()),
									'wx_out_trade_no'  : order_id0,
									'pay_type'     : 'WXPAY',
								},
								'$push' : {
									'wx_notify' : str_xml,
									'history'   : (app_helper.time_str(), 'wxpay', '付款通知:余额不足转入退款')
								}
							})

							return 	'<xml>' \
					  			'<return_code><![CDATA[SUCCESS]]></return_code>' \
					  			'<return_msg><![CDATA[OK]]></return_msg>' \
								'</xml>' 


					# 使用的优惠券失效 # app微信支付，和 公众号微信支付都从这返回

					coupon = []
					if r['coupon']!=None:
						for i in db_user['coupon']:
							if i[0]==r['coupon'][0]: # 这次使用
								#coupon.append((i[0],i[1],i[2],0))
								i2=list(i)
								i2[3]=0
								coupon.append(i2)
							else:
								coupon.append(i)
					else:
						coupon = db_user['coupon']

					# 满30送5元抵用券
					#if float(param.get('total_fee','0'))>=30:
					#	valid = app_helper.time_str(time.time()+3600*24*30, 1)
					#	coupon.append((app_helper.my_rand(), valid, '5.00', 1))
					# 首单送抵用券
					#if db.order_app.find({'user':r['uname'],'status':{'$nin':['TIMEOUT','DUE','CANCEL']},'order_id':{'$ne':order_id}},{'_id':1}).count()==0:
					#	# (id, 有效期, 金额, 是否已用, 门槛) 2015-09-27
					#	valid = app_helper.time_str(time.time()+3600*24*30, 1)
					#	if str(r['shop']) in app_helper.new_coupon2_shop:
					#		print '首单送优惠券(指定店)'							
					#		for i in app_helper.new_coupon2:
					#			coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
					#	else:
					#		print '首单送优惠券'							
					#		for i in app_helper.new_coupon:
					#			coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))

					# 更新优惠券 2015-08-22
					db.app_user.update_one({'$or' : [
						{'uname':r['uname']},{'openid':r['uname']}
					]}, {'$set':{'coupon':coupon}})

					# 邀请码用户送抵用券 2015-10-24
					invitation = db_user.get('invitation', '')
					if invitation!='' and db_user.get('invite_coupon_has_sent', 0)==0: # 已填邀请码并且未送过券
						coupon_user = db.app_user.find_one({'my_invit_code':invitation},{'uname':1})
						if coupon_user:
							# 送邀请码用户抵用券
							print '送邀请码用户抵用券'
							valid = app_helper.time_str(time.time()+3600*24*30, 1)
							db.app_user.update_one({'uname':coupon_user['uname']},{'$push':{
								'coupon' : (app_helper.my_rand(), valid, '5.00', 1, 19.9, 'apple')
							}})
							# 设置已送标志
							db.app_user.update_one({'uname':r['uname']}, {'$set':{'invite_coupon_has_sent':1}})

					
					if order_id[0]=='t': # 拼团订单处理
						# 不修改购物车内容
						b2 = r['cart']

						# 检查是否已在member中
						r1 = db.pt_order.find_one({
							'pt_order_id'   : r['pt_order_id'],
							'member.openid' : r['uname']
						})
						if r1: # 已参团
							status = 'FAIL_TO_REFUND' # 参团失败，等待退款
							comment = ':参团失败-已参团'
							print '参团失败：已参团'
						else:
							# 更新pt_order
							r2 = db.pt_order.find_one_and_update(
								{
									'pt_order_id' : r['pt_order_id'],
									'need'        : { '$gt' : 0 },
									'status'      : { '$in'  : ['OPEN', 'WAIT']}, # 已开团和等待开团状态
								}, 
								{
									'$push' : { 
										'member' : {
											'openid'   : r['uname'],
											'position' : r['position'], 
											'time'     : app_helper.time_str(),
											'order_id' : order_id,
										}
									},
									'$inc' : { 'need' : -1 }
								}
							)

							if r2==None: 							
								# pt_order 状态不是 OPEN 或 need==0, 取消本用户订单
								status = 'FAIL_TO_REFUND' # 参团失败，等待退款
								comment = ':参团失败-已成团'
								print '参团失败：已成团'
							else:
								if r2['need']==1: #  最后一人, 成团！
									db.pt_order.update_one(
										{ 'pt_order_id' : r['pt_order_id']},
										{ 
											'$set' : { 
												'status' : 'SUCC', 
												'succ_time' : app_helper.time_str(),
												'succ_tick' : int(time.time()),
											},
											'$push' : {'history':(app_helper.time_str(), 'wxpay', '拼团成功')}
										}
									)
									
									# 所有团中PAID_AND_WAIT订单成为 PAID，准备拣货
									db.order_app.update_many(
										{ 'pt_order_id' : r['pt_order_id'], 'status':'PAID_AND_WAIT' },
										{
											'$set'  : {'status':'PAID'},
											'$push' : {'history':(app_helper.time_str(), 'wxpay', '拼团成功')}
										}
									)

									# 发消息
									print '发微信通知'
									r3=db.pt_order.find_one({ 'pt_order_id' : r['pt_order_id']},{'member':1})
									for x in r3['member']:
										print app_helper.wx_reply_msg(x['openid'], '您参加的拼团活动已成团，我们会尽快为您安排发货')

									status = 'PAID'
									comment = ':成团'
								else:
									if r2['member']==[]: # 团长开团 
										db.pt_order.update_one(
											{ 'pt_order_id' : r['pt_order_id']},
											{ 
												'$set' : { 
													'status' : 'OPEN', 
													'succ_time' : app_helper.time_str(),
													'succ_tick' : int(time.time()),
												},
												'$push' : {'history':(app_helper.time_str(), 'wxpay', '开团成功')}
											}
										)
									status = 'PAID_AND_WAIT' # 等待成团
									comment = ':等待成团'

					else: # 普通1小时订单: n开头、e开头
						# 正常减库存！
						# item = [ product_id, num, num2, price]
						# k - num 库存数量
						print "修改库存."

						b2 = [] # C端商品
						b3 = [] # B3整箱预售商品
						b3_total = 0.0
						for item in r['cart']:
							# 记录销售量
							db.sku_store.update_one({'product_id' : item['product_id']},
								{'$inc' : {'volume' : float(item['num2'])}}
							)

							# 暂停整箱预售 2015-10-27
							#r3 = db.sku_store.find_one({'product_id' : item['product_id']},
							#	{'list_in_app':1})
							#if r3['list_in_app']==3: # B3商品不需要改库存
							#	b3_total += float(item['price'])
							#	b3.append(item)
							#	item['title'] = item['title']+u'（整箱预售，次日送达）'
							#	b2.append(item)
							#	continue

							# 买一送一
							if item.has_key('numyy'): # v3 2015-10-25
								if item['product_id'] in app_helper.buy_X_give_Y.keys():
									print '买X送Y'
									#item['num2'] = int(float(item['num2']) + float(item['numyy']))
									#item['title'] = item['title'] + u'特惠活动'
							else:
								if item['product_id'] in app_helper.buy_1_give_1:
									print '买一送一'
									lc_num2 = float(item['num2'])
									item['num2'] = int(lc_num2 + lc_num2)
									item['title'] = item['title'].replace(u'买一送一',u'特惠活动')

							# 过滤数量价格为零的
							if item['num2']==0 and float(item['price'])==0.0:
								continue

							# num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
							num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
							r2 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
								{
									'product_id' : item['product_id'],
									'shop'       : r['shop'],
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
								return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
							else:
								b2.append(item)

							# 更新第3方库存 2015-10-10
							app_helper.elm_modify_num(r['shop'], item['product_id'])

						# 检查是否有b3商品, 3种情况
						# 1. b2, b3 都有，拆单
						# 2. 只有b3，站点改为B3站点，保留收货站点
						# 3. 只有b2，保持订单不变
						#print b2
						#print b3
						if len(b3)>0 and (len(b2)-len(b3))>0: # 情况1
							print "拆单"
							r4 = r.copy()
							r4['order_id']     = r4['order_id']+u'-b3'
							r4['shop_0']       = r['shop']
							r4['shop']         = ObjectId(setting.B3_shop)
							r4['cart']         = b3
							r4['status']       = status
							r4['ali_trade_no'] = param.get('trade_no')
							r4['paid_time']    = param.get('gmt_payment')
							r4['paid_tick']    = int(time.time())
							r4['history']      = [(app_helper.time_str(), 'alipay', '付款通知－拆单')]
							r4['total']        = '%.2f' % b3_total
							r4['cost']         = '0.00'
							r4['coupon_disc']  = '0.00'
							r4['first_disc']   = '0.00'
							r4['delivery_fee'] = '0.00'
							r4['due']          = '0.00'
							db.order_app.insert_one(r4) # 增加子订单
						elif len(b3)>0: # 情况 2
							print "订单改到B3站点"
							# 如果订单地址不再配送范围，则由b3直接发出， 2015-10-18
							if r.get('poly_shop', 1)==1: # 默认到店配送
								print 'b3配送到店'
								shop_0 = r['shop']
							else:
								print 'b3直接发货'
								shop_0 = ObjectId(setting.B3_shop)
							db.order_app.update_one({'order_id':order_id},{'$set' : {
								'shop_0' : shop_0, #r['shop'],
								'shop'   : ObjectId(setting.B3_shop),
							}})
						else: # 情况3，什么都不做
							print "订单保持不变"

					# 推送通知
					#if len(r['uname'])==11 and r['uname'][0]=='1':
					#	jpush.jpush('已收到您的付款，我们会尽快处理。', r['uname'])
				else:
					print "重复通知：wxpay"
					b2 = r['cart']

				# 修改订单状态
				t = xml.find('time_end').text
				paid_time = '%s-%s-%s %s:%s:%s' % (t[:4],t[4:6],t[6:8],t[8:10],t[10:12],t[12:])
				db.order_app.update_one({'order_id':order_id},{
					'$set'  : {
						'status'       : status,
						'cart'         : b2,     # 更新购物车  2015-09-11
						'wx_trade_no'  : xml.find('transaction_id').text,
						'paid_time'    : paid_time,
						'paid_tick'    : int(time.time()),
						'wx_out_trade_no'  : order_id0,
						'pay_type'     : 'WXPAY',
						'credit_total' : '%.2f' % float(r.get('use_credit', '0')),
						'wxpay_total'  : '%.2f' % (float(xml.find('total_fee').text)/100.0)
					},
					'$push' : {
						'wx_notify' : str_xml,
						'history'   : (app_helper.time_str(), 'wxpay', '付款通知'+comment)
					}
				})

		return 	'<xml>' \
  			'<return_code><![CDATA[SUCCESS]]></return_code>' \
  			'<return_msg><![CDATA[OK]]></return_msg>' \
			'</xml>' 

##-----------------------------------------------------------------

# 取得主机端口
class WxGetHost:
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='',session_id='')

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)
		if uname:
			# 返回host地址、端口
			host = setting.app_pool[random.randint(0,len(setting.app_pool)-1)]
			print 'host = ', host
			return json.dumps({'ret' : 0, 'data' : {
				'protocol' : 'http',
				#'host'     : setting.app_host, #'app.urfresh.cn',
				'host'     : host,
				'port'     : '12050',
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})



#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
