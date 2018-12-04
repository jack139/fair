#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, random
from bson.objectid import ObjectId
from bson.dbref import DBRef
from config import setting
import helper

db = setting.db_web

url = ('/plat/sku_store_new')

class handler:        # PlatSkuStoreNew
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
			render = helper.create_render()

			base_skus=[]
			db_sku=db.base_sku.find({'available':1},{'name':1}).sort([('name',1)])
			for u in db_sku:
				base_skus.append((u['_id'], u['name']))

			base_shops=[]
			db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark']}}, {'name':1,'type':1})
			for u in db_shop:
				base_shops.append((u['_id'], u['name']))

			return render.sku_store_new(helper.get_session_uname(), helper.get_privilege_name(), 
				base_skus, helper.UNIT_TYPE, helper.CATEGORY, base_shops)
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
			render = helper.create_render()
			user_data=web.input(base_sku='', unit='', shop_online=[], is_pack='', is_pack2='')

			if '' in (user_data.base_sku, user_data.unit):
				return render.info('请正确输入参数！') 

			if '' in (user_data.is_pack, user_data.is_pack2):
				return render.info('请正确输入代码分类和商品分类！') 

			# 取得sku计数
			db_pk = db.user.find_one_and_update(
				{'uname'    : 'settings'},
				{'$inc'     : {'pk_count' : 1}},
				{'pk_count' : 1}
			)

			product_id = '%s%s%s%07d' % (user_data['city'], user_data['is_pack'], user_data['is_pack2'], db_pk['pk_count'])
			list_in_app = int(user_data['list_in_app']) if user_data['is_pack2']!='2' else 0
			online=[]
			for i in user_data['shop_online']:
				online.append(ObjectId(i))
			r = db.sku_store.insert_one({
				'product_id'    : product_id,
				'base_sku'      : DBRef('base_sku', ObjectId(user_data['base_sku'])), # DBRef
				'category'      : user_data['category'],
				'fresh_time'    : int(user_data['fresh_time']),
				#'unit_num'      : int(user_data['unit_num']),
				'unit'          : user_data['unit'],
				#'price'         : '%.2f' % float(user_data['price']),
				'special_price' : '%.2f' % float(user_data['special_price']),
				'ref_price'     : '%.2f' % float(user_data['ref_price']),
				'ref_cost'      : '%.2f' % float(user_data['ref_cost']),
				'min_price'     : '%.2f' % float(user_data['min_price']),
				'max_price'     : '%.2f' % float(user_data['max_price']),
				'maximun'       : int(user_data['maximun']),
				'is_pack'       : int(user_data['is_pack2']), # 2015-09-22
				'is_gift'       : int(user_data['is_gift']),
				'is_onsale'     : int(user_data['is_onsale']),
				'shipping'      : int(user_data['shipping']),
				'free_delivery' : int(user_data['free_delivery']),
				'wxpay_only'    : int(user_data['wxpay_only']),
				'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
				#'online'        : int(user_data['online']),
				'online'        : online,
				'first_order'   : int(user_data['first_order']),
				# 称重商品不允许网上销售
				'list_in_app'   : list_in_app,
				'app_title'     : user_data['app_title'],
				'promote'       : int(user_data['promote']),
				'sort_weight'   : int(user_data['sort_weight']),
				'available'     : int(user_data['available']),
				'note'          : user_data['note'],
				'volume'        : random.randint(150,200),
				'history'       : [(helper.time_str(), helper.get_session_uname(), '新建')], # 纪录操作历史
			})

			# 新建sku, 不需要刷新inventory的list_in_app属性

			# 给所有站点建立零库存
			db_shop = db.base_shop.find({},{'_id':1})
			for s in db_shop:
				# 新的库存记录
				shop_online = 1 if online==[] or s['_id'] in online else 0
				db.inventory.insert_one({
					'sku'        : r.inserted_id, # 新sku的id
					'shop'       : s['_id'],
					'product_id' : product_id,
					'price'      : '%.2f' % float(user_data['ref_price']),
					'cost_price' : '%.2f' % float(user_data['ref_cost']), # 参考成本
					'weight'     : '0',
					'online'     : min(int(user_data['available']), shop_online), 
					'num'        : 0,
					'audit'      : -1,
					'list_in_app': list_in_app,
					'first_order': int(user_data['first_order']),
					'sort_weight': int(user_data['sort_weight']), 
					'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
					'category'   : user_data['category'],
					'history'    : [(helper.time_str(), helper.get_session_uname(), '新建库存为 0')], # 纪录操作历史
				})

			db.base_sku.update_one({'_id':ObjectId(user_data['base_sku'])},{'$inc':{'refer':1}})
			return render.info('成功保存！','/plat/sku_store')
		else:
			raise web.seeother('/')
