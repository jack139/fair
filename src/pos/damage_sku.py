#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/pos/damage_sku')

# 库存单品报损
class handler:       
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			user_data=web.input(sku='')

			if user_data.sku=='':
				return render.info('错误的参数！')  

			# 检查用户是否有此店权限
			db_shop = helper.get_shop_by_uid()

			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')

			db_sku=db.sku_store.find_one({'_id':ObjectId(user_data.sku)})
			if db_sku!=None:
				base_sku=db.dereference(db_sku['base_sku'])
				return render.damage_sku(helper.get_session_uname(), 
					helper.get_privilege_name(), db_sku, 
					{'name' : base_sku['name'],'original' : base_sku['original']}, 
					helper.UNIT_TYPE, 
					(str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]),
					helper.get_inventory(ObjectId(user_data.sku), db_shop['shop']))
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			user_data=web.input(product_id='',weight='')

			if '' in (user_data.product_id,user_data.weight):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			#  取得门店id
			db_shop = helper.get_shop_by_uid()

			# 报损数量／重量
			if user_data['product_id'][2] in ('1','3'):
				weight = int(user_data['weight'])
			else:
				weight = float(user_data['weight'])

			db.order_damage.insert_one({
				'shop'         : db_shop['shop'],
				'product_id'   : user_data['product_id'],
				'num'          : '%.2f' % weight,
				'history'      : [(helper.time_str(), helper.get_session_uname(), '报损操作')], # 纪录操作历史
			})

			# 调整站点库存，
			r = db.inventory.update_one( # u-prod
				{
					'shop'       : db_shop['shop'],
					'product_id' : user_data['product_id'],
				},
				{ 
					'$inc'  : { 'num' : 0-weight}, # 减少库存
					'$push' : { 'history' : (helper.time_str(), 
						helper.get_session_uname(), '报损操作导致库存减少 %.2f ' % float(weight))},
				}
			)
			# 更新第3方库存 2015-10-10
			helper.elm_modify_num(db_shop['shop'], user_data['product_id'])

			return render.info('已报损！数量：%.2f。' % weight, '/pos/inventory')
		else:
			raise web.seeother('/')
