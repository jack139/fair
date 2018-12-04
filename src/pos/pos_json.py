#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/pos_json')

# 返回指定sku的信息
class handler:        #class PosPosJson: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			user_data=web.input(product_id='', weight='0')

			if user_data.product_id=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 查库存信息
			db_invent=db.inventory.find_one({
				'product_id' : user_data.product_id, 
				'shop'       : db_shop['shop'],
			})
			if not db_invent:
				return json.dumps({'ret' : -1, 'msg' : '本店未查此商品！'})

			# 线下店不检查 online
			#if db_invent['online']==0:
			#	return json.dumps({'ret' : -1, 'msg' : '该商品已下架！'})

			if user_data.product_id[0]=='w' and db_invent['num']<=0:
				return json.dumps({'ret' : -1, 'msg' : '此商品为称重商品，已销售一次，不能重复销售！'})

			# 查sku商品信息
			db_sku=db.sku_store.find_one({'_id' : db_invent['sku']})
			if not db_sku:
				return json.dumps({'ret' : -1, 'msg' : '未查到商品信息！'})

			# 查base_sku
			base_sku=db.dereference(db_sku['base_sku'])

			# 返回结果
			ret = {'ret': 0, 'data':{
				'product_id'   : db_invent['product_id'],
				'name'         : base_sku['name'],
				'weight'       : 0,
				'weight_price' : '',
				'unit_name'    : helper.UNIT_TYPE[db_sku['unit']],
				'price'        : db_invent['price'],
				'is_pack'      : db_sku['is_pack'],
				'invent_num'   : db_invent['num'], 
			}}

			if db_invent['product_id'][0]=='w':
				ret['data']['weight'] = db_invent['weight']
				ret['data']['weight_price'] = db_invent['total'] if db_invent.has_key('total') else ''
			elif db_invent['product_id'][2] in ['1', '3']:
				ret['data']['weight'] = 1
				ret['data']['weight_price'] = db_invent['price']
			elif db_invent['product_id'][2]=='2': # 现场称重
				wt = float(user_data.weight)
				tl = float(db_invent['price']) * wt
				ret['data']['weight'] = '%.2f' % wt
				ret['data']['weight_price'] = '%.2f' % tl

			return json.dumps(ret)
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})

