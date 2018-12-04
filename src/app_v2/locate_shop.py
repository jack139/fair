#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper, lbs

db = setting.db_web

url = ('/app/(v2|v3)/locate_shop')

# 定位门店
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', type='', data='', gps='', sign='')

		if '' in (param.app_id, param.type, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.type not in ['GPS', 'NAME', 'LOC']:
			return json.dumps({'ret' : -7, 'msg' : 'type参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.type, param.data, param.gps])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 准备用户坐标
		print param.type.encode('utf-8'), param.data.encode('utf-8')
		if param.type=='NAME':
			ret, loc = lbs.addr_to_loc(param['data'].encode('utf-8'))
			print ret, loc
			if ret<0:
				# 重试一次，网络可能会失败
				ret, loc = lbs.addr_to_loc(param['data'].encode('utf-8'))
				print ret, loc
				if ret<0:
					loc = {'lat': 0, 'lng': 0}
		elif param.type=='GPS':
			loc0 = param.data.split(',') # 31.20474193,121.620708272
			if len(loc0)<2 or '' in loc0:
				loc = {'lat': 0, 'lng': 0}
			else:
				ret, loc0 = lbs.geo_convert(float(loc0[0]), float(loc0[1]))
				if ret==0:
					loc = {'lat': loc0[0]['y'], 'lng': loc0[0]['x']}
				else:
					loc = {'lat': 0, 'lng': 0}
		elif param.type=='LOC': # 使用联想地址提供的坐标（百度坐标，不需要转换）
			loc0 = param.data.split(',') # 31.20474193,121.620708272
			loc = {'lat': float(loc0[0]), 'lng': float(loc0[1])}

		print loc

		# 找最近距离的店
		poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
		if poly_shop==None:
			print '不在配送范围内'
			#return json.dumps({'ret' : -6, 'msg' : '很抱歉，普通商品无法配送到当前收货地址，整箱预售商品可正常购买'})
			return json.dumps({'ret' : -6, 'msg' : '很抱歉，收货地址不在配送范围内，请更改地址'})

		# 计算gps坐标到站点距离
		distance = 0
		if param.gps!='':
			loc0 = param.gps.split(',') # 31.20474193,121.620708272 纬度，经度
			if len(loc0)==2:
				distance = lbs.geo_distance(loc_shop['lat'],loc_shop['lng'],
					float(loc0[0]),float(loc0[1]))

		# 返回多边形匹配shop
		print 'choose:', poly_shop[1].encode('utf-8')

		if version=='v2':
			ret_data = {'ret' : 0, 'data' : {
				'shop_id'   : str(poly_shop[0]), 
				'shop_name' : poly_shop[1],
				#'address'   : poly_shop[2],
				'distance'  : int(distance),
				'alert'     : False, #True if distance>app_helper.max_alert_distance else False,
				'message'   : ('您当前定位的地址距收货地址超过%d公里，请确认后购买' % app_helper.max_alert_distance) if distance>app_helper.max_alert_distance else '',
			}}
		elif version=='v3':
			# by 站点 配送费
			str_shop = str(poly_shop[0])
			if str_shop in app_helper.delivery_by_shop.keys():
				delivery_fee = app_helper.delivery_by_shop[str_shop]['delivery_fee']
				free_delivery = app_helper.delivery_by_shop[str_shop]['free_delivery']
			else:
				delivery_fee = app_helper.delivery_fee
				free_delivery = app_helper.free_delivery

			# by 站点， banner
			if str_shop in app_helper.BANNER_shop.keys():
				BANNER = app_helper.BANNER_shop[str_shop]
				BANNER_URL = app_helper.BANNER_URL_shop[str_shop]
			else:
				BANNER = app_helper.BANNER
				BANNER_URL = app_helper.BANNER_URL

			ret_data = {'ret' : 0, 'data' : {
				'shop_id'   : str_shop, 
				'shop_name' : poly_shop[1],
				#'address'   : poly_shop[2],
				'distance'  : int(distance),
				'alert'     : False, #True if distance>app_helper.max_alert_distance else False,
				'message'   : ('您当前定位的地址距收货地址超过%d公里，请确认后购买' % app_helper.max_alert_distance) if distance>app_helper.max_alert_distance else '',
				'delivery_fee'  : '%.2f' % delivery_fee,
				'free_delivery' : '%.2f' % free_delivery,
				'first_promote' : '%.2f' % app_helper.first_promote,
				'banner'        : BANNER,
				'banner_url'    : BANNER_URL,
			}}
			#print ret_data

		return json.dumps(ret_data)
