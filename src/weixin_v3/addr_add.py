#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper, lbs

db = setting.db_web

url = ('/wx/addr_add')

# 新增收货地址
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', name='', tel='', addr='', city='')

		if '' in (param.name, param.tel, param.addr, param.city):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			# 判断地址是否有对应门店，否则不在送货范围内
			alert = False
			sort_tick = int(time.time())
			message = ''

			# 获得 收货地址 坐标, 设置城市， v3
			ret, loc = lbs.addr_to_loc(param.addr.strip().encode('utf-8'), city=param.city.strip().encode('utf-8'))
			print ret, loc
			if ret<0:
				loc = {'lat': 0, 'lng': 0}
				alert = False #True
				message = '地址定位失败，请重新输入地址'
				sort_tick = 0
			else:
				poly_shop, loc_shop = lbs.locate_shop((loc['lat'],loc['lng']))
				if poly_shop==None:
					print '不在配送范围内'
					alert = False # True  # 拼团不提示
					message = '很抱歉，收货地址不在配送范围内，请更改地址'#，整箱预售商品可正常购买'
					sort_tick = 0

			# 更新个人资料
			new_addr = (
				app_helper.my_rand(),
				param.name.strip(),
				param.tel.strip(), 
				param.addr.strip(),
				sort_tick,
				loc,
				'', # app 的title
				'', # app 的detail
				param.city.strip(),
			)
			r = db.app_user.update_one({'openid':uname['openid']}, {'$push' : {'address' : new_addr}})

			# 返回
			return json.dumps({'ret' : 0, 'data' : {
				'addr_id'  : new_addr[0],
				'alert'    : alert,
				'message'  : message,
			}})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
