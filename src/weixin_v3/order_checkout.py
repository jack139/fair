#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper, lbs

db = setting.db_web

url = ('/wx/order_checkout')

def quick(L):
	if len(L) <= 1: return L
	return quick([a for a in L[1:] if float(a['cash']) > float(L[0]['cash'])]) + L[0:1] + quick([b for b in L[1:] if float(b['cash']) <= float(L[0]['cash'])])


def checkout(uname, param):
	db_user = db.app_user.find_one({'openid':uname['openid']}, #, 'mice':{'$ne':1}},
		{'coupon':1, 'address':1, 'credit':1, 'mice':1})
	if db_user==None: # 不应该发生
		return {'ret' : -9, 'msg' : '未找到用户信息'}

	# 检查mice, 排除白名单
	if db_user.get('mice')==1 and uname['uname'] not in app_helper.WHITE_LIST:
		print 'mice !!!'
		return {'ret' : -9, 'msg' : '未找到用户信息'}

	# 先要核对送货地址是否在门店送货范围内!!!!!!! -- 需补充

	# 查找shop
	db_shop = db.base_shop.find_one({'_id':ObjectId(param['shop_id'])})
	if db_shop==None:
		return {'ret' : -6, 'msg' : 'shop_id错误'}

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

	# 多边形检查
	poly_shop = lbs.check_in_poly((loc['lat'],loc['lng']), db_shop.get('poly_xy', []))
	if poly_shop==None:
		return {'ret' : -6, 'msg' : 'shop_id错误'}

	# 调整地址排序时间 2015-11-9
	new_addr = []
	for i in db_user['address']:
		if i[0]==param['addr_id']:
			i2=list(i)
			if len(i2)>=5:
				i2[4] = int(time.time())
			else: # 兼容最早早早版本，没时间的
				i2.extend([int(time.time())])
			new_addr.append(i2)
		else:
			new_addr.append(i)

	db.app_user.update_one({'openid':uname['openid']}, {'$set' : {'address' : new_addr}})


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
				return {'ret' : -9, 'msg' : '黄牛下单1'}
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
	#print cart

	if len(cart)==0:
		return {'ret' : -5, 'msg' : '购物车无数据'}
	'''
	if param['order_id']=='':
		#cc = 1
		#while cc!=None:
		#	# 取得sku计数, 不与线下order共用
		#	db_sa = db.user.find_one_and_update(
		#		{'uname'    : 'settings'},
		#		{'$inc'     : {'app_count' : 1}},
		#		{'app_count' : 1}
		#	)
		#	order_id = 'n%06d' % db_sa['app_count']
		#	# 防止订单号重复
		#	cc = db.order_app.find_one({'order_id'  : order_id},{'_id':1})
		order_id = app_helper.get_new_order_id('vx')
		print 'new order_id', order_id
	else:
		order_id = param['order_id']

		cc = db.order_app.find_one({
			#'uname'     : {'$in':uname.values()}, # 防止app的bug，重复order_id
			'order_id'  : order_id,
		},{'status':1,})
		if cc!=None and cc['status']!='DUE': # 检查订单状态，只有due才可以checkout
			print "BUG! order_id status"
			return {'ret' : -99, 'msg' : '订单状态错误'}
	'''
	# 订单状态：DUE, PAID, ONROAD, COMPLETED, CANCELED, FINISH
	# 默认运费 5元，免邮门槛 29元
	order = {
		'status'   : 'DUE',
		'uname'    : uname['openid'],
		'shop'     : db_shop['_id'],
		'user'     : uname['openid'],
		'order_id' : '', #order_id,
		'order_source' : 'weixin', # 2015-10-20
		'address'  : address, # 收货地址
		'coupon'   : coupon,  # 使用的优惠券
		'cart'     : [],
		'cost'         : '0.00', # 成本合计，参考
		'total'        : '0.00', # 价格小计，加项
		'coupon_disc'  : '0.00', # 优惠券抵扣，减项
		'first_disc'   : '0.00', # 首单立减， 减项
		'delivery_fee' : '0.00', # 运费，加项
		'due'          : '0.00', # 应付价格
		'openid'       : uname['openid'],
		'app_uname'    : uname['uname'],
		'uname_id'     : db_user['_id'],
		'type'         : 'HOUR',  # 订单类型， 2015-11-19
		# for processor
		'next_status'    : '',
		'lock'           : 0,
		'man'            : 0,
		'retry'          : 0,
		'comment'        : '',	
		'b_time'         : int(time.time()),
		'e_time'         : int(time.time()),
		'deadline'       : int(time.time()+60*15),
		'poly_shop'      : 1 if poly_shop else 0, # 是否匹配到门店 2015-10-18
		'credit_total'   : '0.00', # 余额支付金额 2015-11-24
		'wxpay_total'    : '0.00', # 微信支付金额 
		'alipay_total'   : '0.00', # 支付宝支付金额 
		'use_credit'     : '0.00', # 部分支付时，余额支付金额
		'due3'           : '0.00', # 第3方应付金额   use_credit + due3 = due
	}

	# 统计旧订单数，为0则是首单 2015-09-29
	old_order_num = db.order_app.find({'user':{'$in':uname.values()}, 
		'status':{'$nin':['DUE','TIMEOUT','CANCEL']}},{'_id':1}).count()

	# item = {
	#      “product_id” : “k000011”, 
	#      “num”        : “5”, 
	# }
	# 应该只有 k-prod
	cart_to_return = []
	cart_to_return_b3 = []
	cate_001 = 0
	b3_sku = 0
	all_sku = 0
	num_change = 0
	buy_limit = 0
	only_one = 0
	for item in cart:
		is_b3 = False
		# sku
		db_sku=db.sku_store.find_one({'product_id': item['product_id']},{
			'app_title'     : 1,
			'is_onsale'     : 1,
			'special_price' : 1,
			'ref_price'     : 1,
			'maximun'       : 1,
			'list_in_app'   : 1,
		})
		if db_sku==None: # 应该不会发生
			print 'Error: db_sku==None'
			continue

		if db_sku['list_in_app']== -3: # B3 整箱预售 # 关闭 B3 2015-10-27
			r = db.inventory.find_one(  # 线上销售要检查库存
				{
					'product_id'  : item['product_id'],
					'list_in_app' : {'$ne' : 0},
					'shop'        : ObjectId(setting.B3_shop),
				},
				{
					'cost_price'  : 1, 
					'ref_prod_id' : 1, 
					'price'       : 1, 
					'sku'         : 1, 
					'num'         : 1, 
					'category'    : 1,
					'first_order' : 1
				}
			)
			b3_sku += 1
			is_b3 = True # 标记是B3商品， v3
		elif poly_shop: # 门店库存
			r = db.inventory.find_one(  # 线上销售要检查库存
				{
					'product_id'  : item['product_id'],
					'list_in_app' : {'$ne' : 0},
					'shop'        : db_shop['_id'],
				},
				{
					'cost_price'  : 1, 
					'ref_prod_id' : 1, 
					'price'       : 1, 
					'sku'         : 1, 
					'num'         : 1, 
					'category'    : 1,
					'first_order' : 1
				}
			)
		else: # 不在送货范围
			r = None

		if r: # 如果库存数据中没此sku，会忽略掉，此情况应该不会发生
			new_num = int(item['num'])
			new_num = new_num if new_num<=r['num'] else r['num']
			new_num = max(0, new_num) # 发现过小于零的情况，微信

			# 检查是不是 001 (水果) 分类
			if r['category']=='001':
				cate_001 += 1

			# 检查是否限购
			if db_sku['maximun']>0: 
				'''
				# 每日限购，生成当天的时间tick
				tday = app_helper.time_str(format=1)
				begin_d = '%s 00:00:00' % tday
				end_d = '%s 23:59:59' % tday
				begin_t = int(time.mktime(time.strptime(begin_d,"%Y-%m-%d %H:%M:%S")))
				end_t = int(time.mktime(time.strptime(end_d,"%Y-%m-%d %H:%M:%S")))

				print begin_d, end_d, begin_t, end_t

				# 检查时间段内购买记录
				c = db.order_app.find({
					'uname'           : {'$in': uname.values()},
					'order_id'        : {'$ne':order_id},
					'status'          : {'$ne':'TIMEOUT'},
					'cart.product_id' : item['product_id'],
					'$and'   : [{'b_time' : {'$gt' : begin_t}},
						    {'b_time' : {'$lt' : end_t}}],
				}, {'_id':1}).count()
				print 'findings: ',c
				if c>0: # 限购商品只允许购买1次
					new_num=0
				else:
					new_num=min(new_num, db_sku['maximun'])
					print 'limit : ',new_num
				'''
				# 每单限购
				if new_num>db_sku['maximun']:
					new_num = db_sku['maximun']
					print 'limit : ',new_num

			# 首单可见商品，非首单用户 2015-09-30
			if r.has_key('first_order') and r['first_order']==1 and old_order_num>0:
				# 非首单用户，不让购买，还是有人能买到，靠！
				new_num = 0

			# v3 检查是否是互斥商品
			if item['product_id'] in app_helper.only_one:
				if only_one>0: 
					# 已有互斥商品，此商品清零
					new_num = 0
				else:
					only_one += 1

			# v3 检查是否买X送Y
			if item['product_id'] in app_helper.buy_X_give_Y.keys():
				numX = app_helper.buy_X_give_Y[item['product_id']][0]
				numY = app_helper.buy_X_give_Y[item['product_id']][1]
				#new_num = int(item['num'])
				new_num_give = int(new_num/numX)*numY
				new_num = new_num if new_num+new_num_give<=r['num'] else int(r['num']/(numX+numY))*numX
				new_num = max(0, new_num) # 预防小于零的情况
				new_num_give = int(new_num/numX)*numY # 更新赠品数量

			new_item = {
				'product_id' : item['product_id'],
				'num'        : item['num'],
				'num2'       : new_num,
				'price'      : r['price'],
				'title'      : db_sku['app_title'],
			}

			# v3 买X送Y数量
			if item['product_id'] in app_helper.buy_X_give_Y.keys():
				new_item['numyy'] = new_num_give
			else:
				new_item['numyy'] = 0

			if int(new_num)!=int(item['num']):
				num_change += 1

			# 是否有优惠价格
			if db_sku['is_onsale']==1 and \
				float(db_sku['special_price'])<float(r['price']): 
				# 优惠价格比门店价格低
				new_item['price']=db_sku['special_price']

			# 计算总价
			item_price = round(new_num*float(new_item['price']),2)
			new_item['price']='%.2f' % item_price

			if is_b3:
				cart_to_return_b3.append(new_item) 
			else:
				cart_to_return.append(new_item) # 返回到app的cart不包含cost

			cost_price = r['cost_price']

			#if item[0][0]=='w': # w-prod 信息都用 u-prod的替换
			#	new_item['product_id'] = r['ref_prod_id']
			#	new_item['w_id'] = item[0]
			#	# 查询成本, 从对应u-prod当前成本
			#	r2 = db.inventory.find_one({ # u-prod
			#		'shop'       : db_shop['shop'],
			#		'product_id' : r['ref_prod_id'],
			#	}, {'cost_price':1})
			#	cost_price = r2['cost_price']

			# 计算成本
			item_cost = round(new_num*float(cost_price),2)
			new_item['cost'] = '%.2f' % item_cost

			# 加入cart
			order['cart'].append(new_item)

			# 累计售价和成本
			order['total'] = '%.2f' % (float(order['total'])+item_price)
			order['cost'] = '%.2f' % (float(order['cost'])+item_cost)
		else: 
			# 店内未找到库存， ！！！应该不会发生
			new_item = {
				'product_id' : item['product_id'],
				'num'        : item['num'],
				'num2'       : 0,
				'price'      : '0.00',
				'cost'       : '0.00',
				'title'      : db_sku['app_title'],
			}
			cart_to_return.append(new_item) # 返回到app的cart不包含cost
			order['cart'].append(new_item)

			# 记录判断数量变化
			if int(new_item['num2'])!=int(item['num']):
				num_change += 1


	tt = float(order['total'])
	if tt>0:
		# 免邮门槛
		if str(order['shop']) in app_helper.delivery_by_shop.keys():
			delivery_fee = app_helper.delivery_by_shop[str(order['shop'])]['delivery_fee']
			free_delivery = app_helper.delivery_by_shop[str(order['shop'])]['free_delivery']
		else:
			delivery_fee = app_helper.delivery_fee
			free_delivery = app_helper.free_delivery

		#if tt<29: # 免邮门槛 29
		if tt<free_delivery: # 免邮门槛 
			order['delivery_fee'] = '%.2f' % delivery_fee # 运费5元

		# 首单立减 first_promote元, 商品总额大于 first_promote_threshold元
		if cate_001>0 and old_order_num==0:
			# 符合首单条件，且有一个水果商品
			print '首单'
			if str(db_shop['_id']) in app_helper.first_promote2_shop and \
				(tt+float(order['delivery_fee']))>=app_helper.first_promote2_threshold:
				# 站点落在 指定站点范围内，使用首单立减2
				print '首单立减 － 指定站点'
				order['first_disc'] = '%.2f' % app_helper.first_promote2
			elif (tt+float(order['delivery_fee']))>=app_helper.first_promote_threshold:
				# 其他站点使用首单立减1
				print '首单立减'
				order['first_disc'] = '%.2f' % app_helper.first_promote

		# 优惠券, 检查有效期, 优惠券门槛为10元
		if float(order['first_disc'])==0.0 and coupon!=None and \
			coupon[3]==1 and app_helper.time_str(format=1)<=coupon[1]:
			print '检查抵用券'
			if len(coupon)>5 and coupon[5]=='apple' and cate_001<1:
				# 水果券，但没有水果 2015-09-29
				print '水果券没水果'
				order['coupon'] = None
			elif len(coupon)>5 and coupon[5]=='b3' and b3_sku<1:
				# 整箱券，但没有整箱 2015-10-18
				print '整箱券没整箱'
				order['coupon'] = None
			else:
				if len(coupon)>4:
					# (id, 有效期, 金额, 是否已用, 门槛) 2015-09-27
					# 有门槛信息，使用优惠券门槛信息
					if (tt+float(order['delivery_fee']))<coupon[4]:
						order['coupon'] = None
					else:
						order['coupon_disc'] = coupon[2]
				else:
					# 使用默认条件
					if float(coupon[2])==6.0 and (tt+float(order['delivery_fee']))<29.9:
						order['coupon'] = None
					elif  float(coupon[2])==9.0 and (tt+float(order['delivery_fee']))<39.9:
						order['coupon'] = None
					elif  (tt+float(order['delivery_fee']))<14.9:
						order['coupon'] = None
					else:
						order['coupon_disc'] = coupon[2]
		else:
			order['coupon'] = None

		# 计算应付：价格合计 - 优惠券 - 首单立减 + 运费
		print (tt+float(order['delivery_fee'])-float(order['coupon_disc'])-float(order['first_disc']))
		print tt,float(order['delivery_fee']),float(order['coupon_disc']),float(order['first_disc'])
		order['due'] = '%.2f' % (tt+float(order['delivery_fee'])-float(order['coupon_disc'])-float(order['first_disc']))

		if float(order['due'])<0:
			order['due'] = '1.00'
		order['due3'] = order['due']

	# 准备可用的优惠券 2015-09-11
	coupon_list = []
	for i in db_user['coupon']:
		if app_helper.time_str(format=1)>i[1]: # 过期抵用券
			continue
		elif i[3]!=1:
			continue

		# 检查优惠券条件 b3_sku
		if tt>0 and float(order['first_disc'])==0.0:
			if len(i)>5 and i[5]=='apple' and cate_001<1: # 水果券没水果
				continue
			if len(i)>5 and i[5]=='b3' and b3_sku<1: # 整箱券没整箱 2015-10-18
				continue
			if len(i)>4: # 带门槛优惠券
				if (tt+float(order['delivery_fee']))<i[4]:
					continue
			else:
				# 过滤不符合条件的优惠券
				if float(i[2])==6.0 and (tt+float(order['delivery_fee']))<29.9:
					continue
				elif float(i[2])==9.0 and (tt+float(order['delivery_fee']))<39.9:
					continue
				elif (tt+float(order['delivery_fee']))<14.9:
					continue
			coupon_list.append({
				'id'     : i[0],
				'valid'  : i[1],
				'cash'   : i[2],
				'status' : 'unused', 
				'msg1'   : '条件1',
				'msg2'   : '条件2',
			})

	coupon_list = quick(coupon_list)

	# 如果没有，则insert
	#db.order_app.update_one({'order_id':order_id}, {
	#	'$set'  : order,
	#	'$push' : {'history'  : (app_helper.time_str(), uname['openid'], '提交结算')}
	#}, upsert=True)
	
	# 保存在用户信息里，微信不回重复登录，所以只保留一处，不用关联session，与app不同
	# 2015-10-29
	db.app_user.update_one({'openid':uname['openid']}, {
		'$set'  : { 'cart_order_wx' : order }
	})


	# 提示信息
	#print all_sku, b3_sku
	if poly_shop==False:
		msg_alert = True
		if b3_sku>0:
			if all_sku>b3_sku:
				#message = '很抱歉，普通商品无法配送到当前地址，商品已更新' #，整箱预售商品可正常购买'
				msg_alert = False
				message = ''
			else: # 只有 b3 商品时不提醒
				msg_alert = False
				message = ''
		else:
			message = '很抱歉，收货地址不在配送范围内，购物车商品已清空'
	else:
		if num_change>0:
			msg_alert = True
			message = '库存不足，已更新商品数量，请查看'
		elif buy_limit>0:
			msg_alert = True
			message = '部分商品限购，已更新商品数量，请查看'
		else:
			msg_alert = False
			message = ''

	hh = time.localtime().tm_hour
	if hh>=9 and hh<20:
		alert_title = False
		cart_title = ''
	else:
		alert_title = True
		if hh>=20 and hh<=23:
			cart_title = '配送时间9:00-20:00，掌柜休息中，预计明日9点送达'
		else:
			cart_title = '配送时间9:00-20:00，掌柜休息中，预计今日9点送达'
	
	if b3_sku>0:
		if hh<16:
			# 明天
			tomorrow_tick = int(time.time()) + 3600*24
			tomorrow = time.strftime("%m月%d日", time.localtime(tomorrow_tick))
			cart_title_b3 = '以下预售商品，预计明天%s送达' % tomorrow
		else:
			# 后天
			the_day_after_tick = int(time.time()) + 3600*24*2
			the_day_after = time.strftime("%m月%d日", time.localtime(the_day_after_tick))
			cart_title_b3 = '以下预售商品，预计后天%s送达' % the_day_after
	else:
		cart_title_b3 = ''

	
	ret_data = {  
			'order_id'     : order['order_id'],  
			'shop_id'      : str(order['shop']),  
			'shop'         : db_shop['name'], # 可能会变，如果地址与门店不匹配的时候
			'addr_id'      : address[0], 
			'cart_num'     : len(order['cart']),
			'cart'         : cart_to_return,
			'cart_b3'      : cart_to_return_b3,
			'total'        : order['total'],
			'coupon_list'  : coupon_list, # 可用的优惠券 
			'coupon'       : coupon[0] if order['coupon'] else '',
			'coupon_disc'  : order['coupon_disc'],
			'first_disc'   : order['first_disc'],
			'delivery_fee' : order['delivery_fee'],
			'due'          : order['due'],
			'credit'       : '%.2f' % db_user.get('credit', 0.0),
			'alert'        : msg_alert,
			'message'      : message,
			'alert_title'  : alert_title,
			'cart_title'   : cart_title,
			'alert_title_b3': True,
			'cart_title_b3': cart_title_b3,
	}

	return {'ret'  : 0,'data' : ret_data}


# 购物车结算，json提交
class handler:        #class PosPosCheckout: 
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', shop_id='', order_id='', addr_id='', coupon_id='', cart='')

		if '' in (param.shop_id, param.addr_id, param.cart):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		print param

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			ret_json = checkout(uname, param)

			print ret_json

			return json.dumps(ret_json)
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})

