#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/invent_online')

# 指定sku上下架
class handler:        #class PosInventOnline: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_INVENTORY'):
			user_data=web.input(product_id='', online='')

			if '' in (user_data.product_id, user_data.online):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			db_invent=db.inventory.update_one({
					'product_id' : user_data.product_id, 
					'shop'       : db_shop['shop'],
				}, {
					'$set':{'online' : int(user_data.online)},
					'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(),
						'上下架标志修改为 %s' % str(user_data.online))},
				}
			)

			return json.dumps({'ret' : 0, 'msg' : '操作完成'})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
