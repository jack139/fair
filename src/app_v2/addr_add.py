#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, lbs

db = setting.db_web

url = ('/app/(v2|v3)/addr_add')

# 新增收货地址
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='',session='',name='',tel='',addr='',title='',detail='',city='',loc='',sign='')

		if '' in (param.app_id, param.session, param.name, param.tel, param.addr, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})	
		# v3 参数检查
		if version=='v3' and '' in (param.title, param.detail, param.city, param.loc):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})	

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			if version=='v2':
				md5_str = app_helper.generate_sign([param.app_id, param.session, param.name, param.tel, param.addr])
			elif version=='v3':
				md5_str = app_helper.generate_sign([param.app_id, param.session, param.name, param.tel, param.addr,
					param.title, param.detail, param.city, param.loc])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			# 判断地址是否有对应门店，否则不在送货范围内
			alert = False
			message = ''

			if version=='v2':
				# 获得 收货地址 坐标
				ret, loc = lbs.addr_to_loc(param.addr.strip().encode('utf-8'))
				print ret, loc
				if ret<0:
					loc = {'lat': 0, 'lng': 0}
					alert = True
					message = '地址定位失败，请重新输入地址'
				else:
					poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
					if poly_shop==None:
						print '不在配送范围内'
						alert = True
						message = '很抱歉，收货地址不在配送范围内，请更改地址' #，整箱预售商品可正常购买'
				# 更新个人资料
				new_addr = (
					app_helper.my_rand(),
					param.name.strip(),
					param.tel.strip(), 
					param.addr.strip(),
					int(time.time()),
					loc,
				)
			elif version=='v3':
				# 使用提示地址的坐标进行匹配
				loc0 = param.loc.split(',') # 31.20474193,121.620708272
				if len(loc0)<2 or '' in loc0:
					loc = {'lat': 0, 'lng': 0}
					alert = True
					message = '地址定位失败，请重新输入地址'
				else:
					loc = {'lat' : float(loc0[0]), 'lng' : float(loc0[1])}
					print loc
					poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
					if poly_shop==None:
						print '不在配送范围内'
						alert = True
						message = '很抱歉，收货地址不在配送范围内，请更改地址' #，整箱预售商品可正常购买'

				# 更新个人资料
				new_addr = (
					app_helper.my_rand(),
					param.name.strip(),
					param.tel.strip(), 
					param.addr.strip(),
					int(time.time()),
					loc,
					param.title.strip(),
					param.detail.strip(),
					param.city.strip(),
				)

			r = db.app_user.update_one({'uname':uname['uname']}, {'$push' : {'address' : new_addr}})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr_id'  : new_addr[0],
				'alert'    : alert,
				'message'  : message,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
