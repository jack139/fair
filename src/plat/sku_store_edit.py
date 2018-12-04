#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from bson.dbref import DBRef
from config import setting
import helper

db = setting.db_web

url = ('/plat/sku_store_edit')

class handler:        # PlatSkuStoreEdit
	def GET(self):
		if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
			render = helper.create_render()
			user_data=web.input(sku='')

			if user_data.sku=='':
				return render.info('错误的参数！')  

			db_sku=db.sku_store.find_one({'_id':ObjectId(user_data.sku)})
			if db_sku!=None:
				base_skus=[]
				db_base=db.base_sku.find({'available':1},{'name':1}).sort([('name',1)])
				for u in db_base:
					base_skus.append((u['_id'], u['name']))

				base_shops=[]
				db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark']}}, {'name':1,'type':1})
				for u in db_shop:
					base_shops.append((u['_id'], u['name']))

				return render.sku_store_edit(helper.get_session_uname(), 
					helper.get_privilege_name(), 
					db_sku, base_skus, helper.UNIT_TYPE, helper.CATEGORY, base_shops)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
			render = helper.create_render()
			user_data=web.input(sku='', base_sku='', unit='', old_base_sku='',
				sort_weight_refresh='',ref_price_refresh2='',ref_price_refresh=[],
				category_refresh='', list_in_app_refresh='', shop_online=[])

			if '' in (user_data.sku, user_data.base_sku, user_data.unit, user_data.old_base_sku):
				return render.info('参数错误！') 

			# 取得现有 ref_price
			db_ref = db.sku_store.find_one({'_id':ObjectId(user_data['sku'])}, {'ref_price':1})
			ref_price_change = round(float(user_data['ref_price'])-float(db_ref['ref_price']),2)
			online=[]
			for i in user_data['shop_online']:
				online.append(ObjectId(i))

			price_refresh=[]
			for i in user_data['ref_price_refresh']:
				price_refresh.append(ObjectId(i))

			update_set={
				'base_sku'      : DBRef('base_sku', ObjectId(user_data['base_sku'])), # DBRef
				'category'      : user_data['category'],
				'fresh_time'    : int(user_data['fresh_time']),
				#'unit_num'      : int(user_data['unit_num']),
				'unit'          : user_data['unit'],
				#'price'         : '%.2f' % float(user_data['price']),
				'special_price' : '%.2f' % float(user_data['special_price']),
				#'ref_price'     : '%.2f' % float(user_data['ref_price']),
				'ref_cost'      : '%.2f' % float(user_data['ref_cost']),
				'min_price'     : '%.2f' % float(user_data['min_price']),
				'max_price'     : '%.2f' % float(user_data['max_price']),
				'maximun'       : int(user_data['maximun']),
				#'is_pack'       : int(user_data['is_pack']),  // 一旦设置，不能修改
				'is_gift'       : int(user_data['is_gift']),
				'is_onsale'     : int(user_data['is_onsale']),
				'shipping'      : int(user_data['shipping']),
				'free_delivery' : int(user_data['free_delivery']),
				'wxpay_only'    : int(user_data['wxpay_only']),
				'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
				#'online'        : int(user_data['online']), // 上下架放到门店库存inventory
				'online'        : online,
				'first_order'   : int(user_data['first_order']),
				'list_in_app'   : int(user_data['list_in_app']),
				'app_title'     : user_data['app_title'],
				'promote'       : int(user_data['promote']),
				'sort_weight'   : int(user_data['sort_weight']),
				'available'     : int(user_data['available']),
				'note'          : user_data['note'],
			}
			if price_refresh==[]: # 只有刷新所有价格时才保存在shu_store中
				update_set['ref_price'] = '%.2f' % float(user_data['ref_price'])
			db.sku_store.update_one({'_id':ObjectId(user_data['sku'])}, {
				'$set'  : update_set,
				'$push' : {
					'history' : (helper.time_str(), helper.get_session_uname(), '修改'), 
				}  # 纪录操作历史
			})

			#db.sku_store.update_one({'_id':ObjectId(user_data['sku'])}, {'$push':{
			#	'history' : (helper.time_str(), helper.get_session_uname(), '修改'), # 纪录操作历史
			#}})

			# 整箱预售，修改所有inventroy分类			
			#if user_data['category']=='006':
			#	db.inventory.update_many({'sku':ObjectId(user_data['sku'])}, {
			#		'$set'  : { 
			#			'category' : user_data['category'],
			#		},
			#		'$push' : { 
			#			'history' : (helper.time_str(), helper.get_session_uname(), '整箱预售')
			#		}, # 纪录操作历史
			#	})

			# 可以优先设置平台参数 2015-09-15
			update_set = { 
				'online'      : int(user_data['available']),
				'first_order' : int(user_data['first_order']),
				'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
			}
			history_txt = ''
			if user_data['category_refresh']=='all':
				update_set['category'] = user_data['category']
				history_txt += ',刷新分类'
			if user_data['ref_price_refresh2']=='all': # 2015-10-31 未选择，则刷新所有
				update_set['price'] = '%.2f' % float(user_data['ref_price'])
				history_txt += ',刷新价格'
			if user_data['sort_weight_refresh']=='all':
				update_set['sort_weight'] = int(user_data['sort_weight'])
				history_txt += ',刷新排序'
			if user_data['list_in_app_refresh']=='all':
				update_set['list_in_app'] = int(user_data['list_in_app'])
				history_txt += ',刷新list_in_app'

			# 根据 available 确定门店库存上下架 2015-06-21
			# 不修改 list_in_app 等app参数，由门店自己修改 2015-08-12
			db.inventory.update_many({'sku':ObjectId(user_data['sku'])}, {
				'$set'  : update_set,
				'$push' : { 
					'history' : (helper.time_str(), helper.get_session_uname(), 
						'门店上架,'+history_txt if int(user_data['available'])==1 else '门店下架,'+history_txt)
				}, # 纪录操作历史
			})

			# 根据online 区别更新各站online, 2015-09-25
			if int(user_data['available'])==1 and online!=[]:
				db.inventory.update_many({
					'sku'  : ObjectId(user_data['sku']),
					'shop' : {'$nin' : online},
				}, { 
					'$set'  : { 'online' : 0 },
					'$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '指定下架')},
				})

			# 根据price_refresh 区别更新各站ref_price, 2015-10-31
			if price_refresh!=[]:
				db.inventory.update_many({
					'sku'  : ObjectId(user_data['sku']),
					'shop' : {'$in' : price_refresh},
				}, { 
					'$set'  : { 'price' : '%.2f' % float(user_data['ref_price']) },
					'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), '刷新价格')},
				})

			if user_data.base_sku!=user_data.old_base_sku:
				db.base_sku.update_one({'_id':ObjectId(user_data['base_sku'])},{'$inc':{'refer':1}})
				db.base_sku.update_one({'_id':ObjectId(user_data['old_base_sku'])},{'$inc':{'refer':-1}})
			return render.info('成功保存！','/plat/sku_store')
		else:
			raise web.seeother('/')
