#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, sys
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

if __name__ == "__main__":
	if len(sys.argv)==1:
		print "usage: python new_shop_inventory.py <shop_id>"
		sys.exit(2)

	shop_id = ObjectId(sys.argv[1]); 

	db_shop = db.base_shop.find_one({'_id':shop_id})
	if db_shop==None:
		print 'Cannot find shop!!!'
	else:
		print 'shop_id: ', str(shop_id), db_shop['name']

		# 取得sku数据
		db_sku = db.sku_store.find({})

		for i in db_sku:
			print i['product_id'], i['ref_price']
			r = db.inventory.find_one_and_update(
				{
					'product_id'  : i['product_id'],
					'shop'        : shop_id,
				},
				{ 
					'$set'  : { 'price'   : i['ref_price']},
					'$push' : { 'history' : (helper.time_str(), 'test', '更新价格')},
				},
				{'num':1}
			)
			if r==None: # 门店新sku
				db.inventory.insert_one({
					'sku'        : i['_id'],
					'shop'       : shop_id,
					'product_id' : i['product_id'],
					'price'      : i['ref_price'],
					'cost_price' : 0, 
					'weight'     : 0,
					'online'     : i['available'],
					'num'        : 0,
					'audit'      : -1,
					'list_in_app': i['list_in_app'],
					'sort_weight': i['sort_weight'], 
					'category'   : i['category'],
					'history'    : [(helper.time_str(), 'test', '初始化库存为 0')], 
				})
				print '新建：',i['product_id']
			else:
				print '更新：',i['product_id']
