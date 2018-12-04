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

			else:
				loc0 = param.data.split(',') # 31.20474193,121.620708272
				loc = {'lat': float(loc0[0]), 'lng': float(loc0[1])}

			# 找最近距离的店
			min_d = 999999
			min_shop = None
			poly_shop = None # 多边形匹配
			db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}})
			for s in db_shop:
				if s.get('app_shop', 1)==0: # 忽略不支持线上销售的店
					continue
				#d=lbs.geo_distance(s['loc']['lat'],s['loc']['lng'],loc['lat'],loc['lng'])
				#print 'd = ', d, min_d
				#if d<s.get('radius', 2) and d<min_d: # 默认半径2公里
				#	min_d=d
				#	min_shop=(s['_id'],s['name'],s['address'])

				# 多边形检查
				poly = s.get('poly_xy', [])
				if len(poly)==0: # 没有多边形数据
					print "缺少多边形数据!"
					continue
				if lbs.wn_PnPoly((loc['lat'],loc['lng']), poly)!=0:
					print 'bingo! poly_shop'
					poly_shop=(s['_id'],s['name'],s['address'])
					break

			if poly_shop==None and min_shop==None:
				print '不在配送范围内'
				return json.dumps({'ret' : -6, 'msg' : '不在配送范围内'})

			if poly_shop==None:
				# 返回最近shop
				print 'choose:', min_shop[1].encode('utf-8')
				return json.dumps({'ret' : 0, 'data' : {
					'shop_id'   : str(min_shop[0]), 
					'shop_name' : min_shop[1],
					'address'   : min_shop[2],
				}})
			else:
				# 返回多边形匹配shop
				print 'choose:', poly_shop[1].encode('utf-8')
				return json.dumps({'ret' : 0, 'data' : {
					'shop_id'   : str(poly_shop[0]), 
					'shop_name' : poly_shop[1],
					'address'   : poly_shop[2],
				}})

		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
