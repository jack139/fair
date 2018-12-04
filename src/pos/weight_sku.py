#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/pos/weight_sku')

class handler:        #class PosWeightSku:        
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
				return render.weight_sku(helper.get_session_uname(), 
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
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			user_data=web.input(sku='', product_id='',weight='',price='')

			if '' in (user_data.sku, user_data.product_id,user_data.weight,user_data.price):
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 检查用户是否有此店权限
			db_shop = helper.get_shop_by_uid()
			#if str(db_shop['shop'])!=user_data.shop:
			#	return json.dumps({'ret' : -1, 'msg' : '无站点管理权限！'})

			#db_sku=db.sku_store.find_one({'product_id':user_data.product_id},{'product_id':1})
			#if db_sku==None:
			#	return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 取得sku计数
			db_wt = db.user.find_one_and_update(
				{'uname'    : 'settings'},
				{'$inc'     : {'wt_count' : 1}},
				{'wt_count' : 1}
			)

			new_prod_id = 'w%06d' % db_wt['wt_count']

			# 计算价格
			weight = float(user_data['weight'])
			weight_price = weight * float(user_data['price'])

			db.inventory.insert_one({
				'sku'         : ObjectId(user_data.sku),
				'shop'        : db_shop['shop'],
				'product_id'  : new_prod_id,
				'ref_prod_id' : user_data.product_id, 
				'price'       : user_data['price'],
				'cost_price'  : '', # w-prod 不记录成本价，实际计算在u-prod中
				'weight'      : '%.2f' % weight,
				'online'      : 1, # 默认 上架
				'num'         : 1,
				'audit'       : -1,
				'total'       : '%.2f' % weight_price,
				'weight_time' : helper.time_str(), # 称重时间，方便盘点统计
				'history'     : [(helper.time_str(), helper.get_session_uname(), '新建库存为 1')], # 纪录操作历史
			})

			# 调整站点库存， 不调整u-prod库存，销货时再调整
			#r = db.inventory.update_one( # u-prod
			#	{
			#		'shop'       : ObjectId(user_data.shop),
			#		'product_id' : user_data.product_id,
			#	},
			#	{ 
			#		'$inc'  : { 'num' : 0-weight},
			#		'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), '称重操作导致库存变化 %.2f ' % (0-weight))},
			#	}
			#)

			# 查询库存
			#r = db.inventory.find_one({ # u-prod
			#	'sku'        : ObjectId(user_data.sku),
			#	'shop'       : ObjectId(user_data.shop),
			#	'product_id' : db_sku['product_id'],
			#}, {'num':1})

			return json.dumps({ # 返回结果，
				'ret'  : 0, 
				'data' : { 
					'product_id' : new_prod_id,
					'weight'     : '%.2f' % weight,
					'total'      : '%.2f' % weight_price,
					'price'      : user_data['price'],
					#'invent_num' : '%.2f' % r['num']  # 剩余库存
				}
			})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
