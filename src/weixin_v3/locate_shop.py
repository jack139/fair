#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import app_helper,lbs

db = setting.db_web

url = ('/wx/locate_shop')

# 定位门店
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', type='', data='')

		if param.type=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.type not in ['GPS', 'NAME']:
			return json.dumps({'ret' : -3, 'msg' : 'type参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			# 准备用户坐标
			if param.type=='NAME':
				ret, loc = lbs.addr_to_loc(param['data'].encode('utf-8'))
				print ret, loc
				if ret<0:
					# 重试一次，网络可能会失败
					ret, loc = lbs.addr_to_loc(param['data'].encode('utf-8'))
					print ret, loc
					if ret<0:
						loc = {'lat': 0, 'lng': 0}

			else: # GPS
				loc0 = param.data.split(',') # 31.20474193,121.620708272
				if len(loc0)<2 or '' in loc0:
					loc = {'lat': 0, 'lng': 0}
				else:
					ret, loc0 = lbs.geo_convert(float(loc0[0]), float(loc0[1]))
					if ret==0:
						loc = {'lat': loc0[0]['y'], 'lng': loc0[0]['x']}
					else:
						loc = {'lat': 0, 'lng': 0}

				#loc = {'lat': float(loc0[0]), 'lng': float(loc0[1])}

			# 找最近距离的店
			poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
			if poly_shop==None:
				print '不在配送范围内'
				#return json.dumps({'ret' : -6, 'msg' : '很抱歉，普通商品无法配送到当前收货地址，整箱预售商品可正常购买'})
				return json.dumps({'ret' : -6, 'msg' : '很抱歉，收货地址不在配送范围内，请更改地址'})

			# by 站点 配送费
			str_shop = str(poly_shop[0])
			if str_shop in app_helper.delivery_by_shop.keys():
				delivery_fee = app_helper.delivery_by_shop[str_shop]['delivery_fee']
				free_delivery = app_helper.delivery_by_shop[str_shop]['free_delivery']
			else:
				delivery_fee = app_helper.delivery_fee
				free_delivery = app_helper.free_delivery

			# by 站点， banner
			if str_shop in app_helper.BANNER_shop_WX.keys():
				BANNER = app_helper.BANNER_shop_WX[str_shop]
				BANNER_URL = app_helper.BANNER_URL_shop_WX[str_shop]
			else:
				BANNER = app_helper.BANNER_WX
				BANNER_URL = app_helper.BANNER_URL_WX

			# 返回多边形匹配shop
			print 'choose:', poly_shop[1].encode('utf-8')
			ret_data = {'ret' : 0, 'data' : {
				'shop_id'   : str(poly_shop[0]), 
				'shop_name' : poly_shop[1],
				'address'   : poly_shop[2],
				'delivery_fee'  : '%.2f' % delivery_fee,
				'free_delivery' : '%.2f' % free_delivery,
				'first_promote' : '%.2f' % app_helper.first_promote,
				'banner'        : BANNER,
				'banner_url'    : BANNER_URL,
			}}
			return json.dumps(ret_data)
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
