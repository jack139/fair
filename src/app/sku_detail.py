#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/sku_detail')

# 查询商品详情
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', shop_id='', product_id='')

		if '' in (param.app_id, param.shop_id, param.product_id, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.shop_id, param.product_id])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 有效的sku
		db_sku=db.sku_store.find_one({'product_id': param.product_id},{
			'product_id'    : 1,
			'base_sku'      : 1,
			'app_title'     : 1,
			'is_onsale'     : 1,
			'special_price' : 1,
			'promote'       : 1, 
			'list_in_app'   : 1,
		})

		base_sku = db.dereference(db_sku['base_sku'])

		# 处理整箱预售
		if db_sku['list_in_app']== -3: # -3 不启动B3销售 
			shop_id = setting.B3_shop # B3整箱预售虚拟店
		else:
			shop_id = param.shop_id

		# 查找商品详情
		db_invent = db.inventory.find_one({
				'shop'        : ObjectId(shop_id),
				'product_id'  : param.product_id,
				'list_in_app' : {'$ne' : 0},
			}, 
			{
				'product_id'  : 1,
				#'category'    : 1, # 品类，从sku_store来的
				#'sort_weight' : 1, 
				'sku'         : 1,
				'price'       : 1, # 门店价
				'num'         : 1, # 库存数
			},
		)

		# 准备返回结果
		data = {
			'product_id' : db_invent['product_id'],
			'title'      : db_sku['app_title'],
			'abstract'   : base_sku['abstract'],
			'price'      : db_invent['price'],
			'num'        : db_invent['num'],
			'promote'    : db_sku['promote'],
			'detail_url' : '',
		}

		# 是否有优惠价格
		if db_sku['is_onsale']==1 and float(db_sku['special_price'])<float(db_invent['price']): 
			# 优惠价格比门店价格低
			data['sale_price']=db_sku['special_price']

		# 图片
		if base_sku.has_key('image'):
			if len(base_sku['image'])>1:
				i = base_sku['image'][1] # 第2张是详情图
			else:
				i = base_sku['image'][0] 
			data['image']=['/%s/%s' % (i[:2], i)]	
			#data['image']=['/%s/%s' % (i[:2], i) for i in base_sku['image']]
		else:
			data['image']=''

		# 返回
		return json.dumps({
			'ret' : 0, 
			'data' : data
		})
