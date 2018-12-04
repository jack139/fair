#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper, lbs

db = setting.db_web

url = ('/wx/pt_order_checkout')

def pt_checkout(uname, param):
	db_user = db.app_user.find_one({'openid':uname['openid']}, #, 'mice':{'$ne':1}},
		{'coupon':1, 'address':1, 'credit':1, 'mice':1})
	if db_user==None: # 不应该发生
		return {'ret' : -99, 'msg' : '未找到用户信息'}

	# 检查mice, 排除白名单
	if db_user.get('mice')==1 and uname['uname'] not in app_helper.WHITE_LIST:
		print 'mice !!!'
		return {'ret' : -99, 'msg' : '未找到用户信息'}

	# 先要核对送货地址是否在门店送货范围内!!!!!!! -- 需补充


	# 查找shop
	#db_shop = db.base_shop.find_one({'_id':ObjectId(param.shop_id)})
	#if db_shop==None:
	#	return {'ret' : -6, 'msg' : 'shop_id错误'}

	# 查询收货地址
	address = None
	for i in db_user['address']:
		if i[0]==param['addr_id']:
			address = list(i)
			break
	if address==None:
		return {'ret' : -7, 'msg' : 'addr_id错误'}

	# 获得 收货地址 坐标
	if len(address)>5: # 使用已有的gps地址
		loc = address[5]
	else:
		ret, loc = lbs.addr_to_loc(address[3].encode('utf-8'))
		if ret<0:
			# 重试一次
			ret, loc = lbs.addr_to_loc(address[3].encode('utf-8'))
			if ret<0:
				loc = {'lat': 0, 'lng': 0}
	print loc

	# 检查是否能匹配到门店
	poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
	if poly_shop==None:
		print '匹配不到门店'

	# poly_shop[0] = id
	# poly_shop[1] = name 
	# poly_shop[2] = address 

	###########################################################################
	# 用收货电话检查黄牛 2015-08-22
	db_recv = db.recv_tel.find_one({'tel':address[2]})
	if db_recv:
		one_more = 0
		if uname['openid'] not in db_recv['unames']: # 补充疑似账号
			db.recv_tel.update_one({'tel':address[2]},{'$push':{'unames':uname['openid']}})
			one_more = 1
		if len(db_recv['unames'])+one_more>10: # 改为10，2015-10-12
			# 发现 mice
			mice = 1
			for b in db_recv['unames']: 
				if b in app_helper.WHITE_LIST: # 过滤白名单相关号码
					mice = 0
					break
			db.app_user.update_many({'uname':{'$in':db_recv['unames']}},{'$set':{'mice':mice}})
			db.app_user.update_many({'openid':{'$in':db_recv['unames']}},{'$set':{'mice':mice}})
			if one_more==1:
				db.app_user.update_one({'openid':uname['openid']},{'$set':{'mice':mice}})
			if mice==1:
				print '!!! mice:', address[2]#, uname, db_recv['unames']
				return {'ret' : -99, 'msg' : '黄牛下单1'}
	else:
		db.recv_tel.insert_one({'tel':address[2],'unames':[uname['openid']]})
		#print 'insert', address[2]

	# 用收货地址检查黄牛, 不准确，不能标注 2015-08-23
	db_recv = db.recv_addr.find_one({'addr':address[3]})
	if db_recv:
		one_more = 0
		if uname['openid'] not in db_recv['unames']:
			db.recv_addr.update_one({'addr':address[3]},{'$push':{'unames':uname['openid']}})
			one_more = 1
		if len(db_recv['unames'])+one_more>10: # 改为10，2015-10-12
			# 发现疑似mice，不标注，因为不确定
			print '!!! maybe a mice:', address[3].encode('utf-8') #, uname['openid'], db_recv['unames']
	else:
		db.recv_addr.insert_one({'addr':address[3],'unames':[uname['openid']]})
		#print 'insert', address[2]

	# 查黄牛－结束
	###########################################################################


	# 查找优惠券
	# 未查到，则不使用优惠券
	coupon = None
	for i in db_user['coupon']:
		if i[0]==param['coupon_id']:
			coupon = list(i)
			break

	# 转换cart数据为json，应该有异常捕获 !!!
	cart = json.loads(param['cart'])
	print cart

	if len(cart)==0:
		return {'ret' : -5, 'msg' : '购物车无数据'}

	#if not cart[0].has_key('tuan_id'):
	#	return {'ret' : -5, 'msg' : '购物车数据错误'}

	# 订单状态：DUE, PAID, ONROAD, COMPLETED, CANCELED, FINISH
	# 默认运费 5元，免邮门槛 29元
	now_tick = int(time.time())

	# 检查活动是否可继续
	db_pt_sku = db.pt_store.find_one({
		'tuan_id'   : cart[0]['tuan_id'],
		'region_id' : { '$in' : [ param['region_id'] ] },
		#'online'    : 1,
	})
	if db_pt_sku == None: # tuan_id 错误 
		return {'ret' : -8, 'msg' : '未找到拼团活动信息'}

	cart[0]['title'] = db_pt_sku['title']

	if db_pt_sku['sale_out']==1:
		return {'ret' : -9, 'msg' : '此拼团活动已售罄'}

	if len(param['pt_order_id'])==0: # 新开团

		# 新开团检查是否下架和过期，已开团不检查
		if param['region_id'] not in db_pt_sku['online']:
			return {'ret' : -9, 'msg' : '很抱歉，该拼团活动刚刚下架，无法继续下单'}

		if db_pt_sku['expire_tick']<now_tick:
			return {'ret' : -9, 'msg' : '很抱歉，该拼团活动刚刚结束，无法继续下单'}

		# 准备新的活动订单
		expire_hour = 24 # 测试1小时
		db_pt_order = {
			'tuan_id'     : cart[0]['tuan_id'], 
			'pt_order_id' : '', # 提交付款后生成
			'region_id'   : param['region_id'],
			'expire_tick' : now_tick+3600*expire_hour, 
			'expire_time' : app_helper.time_str(now_tick+3600*expire_hour),
			'create_tick' : now_tick,
			'create_time' : app_helper.time_str(),
			'leader'      : uname['openid'],
			'member'      : [],
			'need'        : db_pt_sku['tuan_size'] if cart[0]['type']=='TUAN' else 1,
			'type'        : 'TUAN' if cart[0]['type']=='TUAN' else 'SINGLE',
			'status'      : 'WAIT', # 等待开团
		}
		# 身份
		position = 'LEADER'
	else:
		# 已开团，检查是否可参团
		db_pt_order = db.pt_order.find_one({'pt_order_id':param['pt_order_id']})
		if db_pt_order==None:
			return {'ret' : -8, 'msg' : '未找到活动订单'}

		# 新开团检查是否下架和过期，已开团不检查, need == tuan_size
		if (db_pt_order['need']==db_pt_sku['tuan_size']) and (param['region_id'] not in db_pt_sku['online']):
			return {'ret' : -9, 'msg' : '很抱歉，该拼团活动刚刚下架，无法继续下单'}

		if db_pt_order['status']=='SUCC':
			return {'ret' : -9, 'msg' : '很抱歉，您慢了一步，该团已满员无法继续下单'}

		if db_pt_order['status']=='FAIL2':
			return {'ret' : -9, 'msg' : '很抱歉，该商品已售罄，无法继续下单'}

		if db_pt_order['status']=='FAIL1' or db_pt_order['expire_tick']<now_tick:
			return {'ret' : -9, 'msg' : '很抱歉，该拼团活动刚刚结束，无法继续下单'}

		# 检查是否已在此团
		for m in db_pt_order['member']:
			if m['openid']==uname['openid']:
				return {'ret' : -9, 'msg' : '你已参加此团，不能重复参团！'}

		# 身份
		if len(db_pt_order['member'])==1:
			position = 'SCEOND'
		else:
			position = 'MEMBER'

	order = {
		'status'         : 'DUE',
		'uname'          : uname['openid'],
		'shop_0' : poly_shop[0] if poly_shop!=None else ObjectId(setting.PT_shop[db_pt_order['region_id']]),
		'shop'           : ObjectId(setting.PT_shop[db_pt_order['region_id']]),
		#'shop_0'         : poly_shop[0] if poly_shop!=None else '',
		'user'           : uname['openid'],
		'order_id'       : '', #order_id,
		'order_source'   : 'wx_tuan', # 2015-10-20
		'address'        : address, # 收货地址
		'coupon'         : coupon,  # 使用的优惠券
		'cart'           : cart,  # 购物车
		'cost'           : '0.00', # 成本合计，参考
		'total'          : '0.00', # 价格小计，加项
		'coupon_disc'    : '0.00', # 优惠券抵扣，减项
		'first_disc'     : '0.00', # 首单立减， 减项
		'delivery_fee'   : '0.00', # 运费，加项
		'due'            : '0.00', # 应付价格
		'openid'         : uname['openid'],
		'app_uname'      : uname['uname'],
		'uname_id'       : db_user['_id'],
		# for processor
		'next_status'    : '',
		'lock'           : 0,
		'man'            : 0,
		'retry'          : 0,
		'comment'        : '',	
		'b_time'         : int(time.time()),
		'e_time'         : int(time.time()),
		'deadline'       : int(time.time()+60*15),
		# 拼团使用
		'pt_order_id'    : param['pt_order_id'],
		'type'           : db_pt_order['type'],
		'region_id'      : db_pt_order['region_id'],
		'position'       : position,
	}

	if order['type']=='TUAN': # 拼团价格
		order['total'] = order['due'] = db_pt_sku['tuan_price']
	else: #  单人购价格
		order['total'] = order['due'] = db_pt_sku['price']

	if float(order['due'])<0:
		order['due'] = '0.10'
	
	# 保存在用户信息里，微信不回重复登录，所以只保留一处，不用关联session，与app不同
	if len(param['pt_order_id'])==0: # 新开团
		update_set = { 
			'cart_order_wx' : [order, db_pt_order],
		}
	else:
		update_set = { 
			'cart_order_wx' : [order],
		}
	db.app_user.update_one({'openid':uname['openid']}, {'$set'  : update_set})

	image_host = 'http://%s/image/product' % setting.image_host

	# 返回信息
	position = 'VISITOR'
	for i in db_pt_order['member']:
		if i['openid']==uname['openid']:
			position = i['position']
			break
	ret_data = {
		'region_id'   : order['region_id'],
		'addr_id'     : address[0],
		'cart'        : [
			{
				'tuan_id' : cart[0]['tuan_id'],
				'title1'  : db_pt_sku['title'],
				'image'   : ['%s/%s/%s' % (image_host, x[:2], x) for x in db_pt_sku['image']],
				'status'  : db_pt_order['status'],  
				'price'   : order['total'],
				'type'    : '%d人团'%db_pt_sku['tuan_size'] if order['type']=='TUAN' else '单人购买',
			},
		],
		'coupon_list' : [],
		'total'       : order['total'], 
		'coupon'      : order['coupon'], 
		'coupon_disc' : order['coupon_disc'],
		'due'         : order['due'], 
		'alert_title' : True,
		'cart_title'  : '免配送费，组团成功后我们会尽快为您安排发货' if order['type']=='TUAN' else '免配送费，下单后我们会尽快为您安排发货',
		'position'    : position,
		'need'        : db_pt_order['need'], 
	}

	return {'ret'  : 0,'data' : ret_data}


# 拼团购物车结算，json提交
class handler:        #class PosPosCheckout: 
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', region_id='', 
			addr_id='', coupon_id='', cart='', pt_order_id='')

		print param

		if '' in (param.region_id, param.addr_id, param.cart):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		#print param

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			ret_json = pt_checkout(uname, param)

			print ret_json

			return json.dumps(ret_json)
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})

