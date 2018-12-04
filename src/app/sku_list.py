#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/sku_list')

# 查询商品，允许分段查询返回
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', shop_id='', category='', page_size='', page_index='')

		if '' in (param.app_id, param.shop_id, param.category, param.page_size, param.page_index, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if not (param.page_size.isdigit() and param.page_index.isdigit()): 
			return json.dumps({'ret' : -4, 'msg' : 'page参数错误'})

		if len(param.shop_id)<24:
			return json.dumps({'ret' : -2, 'msg' : 'shop_id参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.shop_id,
			param.category, param.page_size, param.page_index])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		# 处理整箱预售
		if param.category=='-3': # -3 不启动B3销售
			shop_id = setting.B3_shop # B3整箱预售虚拟店
		else:
			shop_id = param.shop_id

		# 查找商品信息清单
		# 分页返回 find().skip(page_size*page_index).limit(page_size)
		'''
		db_invent = db.inventory.find({
				'shop'        : ObjectId(shop_id),
				'category'    : param.category,
				'list_in_app' : {'$ne' : 0},
				'online'      : 1,
				#'num'         : {'$gt' : 0}, # 只显示有库存的商品
			}, 
			{
				'product_id'  : 1,
				'category'    : 1, # 品类，从sku_store来的
				'sort_weight' : 1, 
				'sku'         : 1,
				'price'       : 1, # 门店价
				'num'         : 1, # 库存数
			},
			skip  = int(param.page_size)*int(param.page_index), 
			limit = int(param.page_size)
		).sort([('sort_weight',1), ('_id',1)])
		'''

		# 取所有商品数据 2015-10-29
		db_invent = db.inventory.find({
				'shop'        : ObjectId(shop_id),
				'category'    : param.category,
				'list_in_app' : {'$ne' : 0},
				'online'      : 1,
				#'num'         : {'$gt' : 0}, # 只显示有库存的商品
			}, 
			{
				'product_id'  : 1,
				'category'    : 1, # 品类，从sku_store来的
				'sort_weight' : 1, 
				'sku'         : 1,
				'price'       : 1, # 门店价
				'num'         : 1, # 库存数
			},
		).sort([('sort_weight',1), ('_id',1)])

		# 库存小于零的沉底 2015-10-29
		db_invent2 = []
		db_num_0 = []
		for s in db_invent:
			if int(s['num'])>0:
				db_invent2.append(s)
			else:
				db_num_0.append(s)
		db_invent2.extend(db_num_0)

		# 取指定区间的 2015-10-29
		start_pos = int(param.page_size)*int(param.page_index)
		end_pos = start_pos + int(param.page_size)
		db_invent3 = db_invent2[start_pos:end_pos]

		invent = []
		skus = []
		for s in db_invent3: 
			skus.append(s['sku'])
			invent.append((
				s['sku'],  #0
				s['price'],    #1
				s['product_id'], #2
				s['num'], #3
			))  

		# 有效的sku
		db_sku=db.sku_store.find({'_id':{'$in':skus}} ,{
			'product_id'    : 1,
			'base_sku'      : 1,
			'app_title'     : 1,
			'is_onsale'     : 1,
			'special_price' : 1,
			'promote'       : 1, 
			'maximun'       : 1,
		}).sort([('_id',1)])

		skus = {}
		for u in db_sku:
			base_sku = db.dereference(u['base_sku'])

			skus[u['_id']]=(
				base_sku['name'],   #0
				base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
				u['app_title'],   #2
				u['is_onsale'],   #3
				u['special_price'],   #4
				base_sku['original'],   #5
				u['promote'],   #6
				u['maximun'],   #7
			)

		data = []
		for i in invent:
			# 调整价格显示，整数价格不显示 .00， 未适应旧版ios app 2015-09-13
			if int(float(i[1]))*1.0==float(i[1]):
				show_price = u'%d ' % int(float(i[1]))
			else:
				show_price = i[1]
			#print show_price.encode('utf-8')

			# 准备数据
			new_one = {
				'product_id' : i[2],
				'title'      : skus[i[0]][2],
				#'original'   : skus[i[0]][5],
				'price'      : show_price,
				#'num'        : min(i[3],skus[i[0]][7]) if skus[i[0]][7]>0 else i[3], # 限购
				'num'        : max(int(i[3]),0),
				'promote'    : skus[i[0]][6],
				'image'      : '/%s/%s' % (skus[i[0]][1][:2], skus[i[0]][1]),
			}
			if skus[i[0]][3]==1 and float(skus[i[0]][4])<float(i[1]): # 优惠价格比门店价格低
				new_one['sale_price'] = skus[i[0]][4],
			data.append(new_one)

		# 返回最近shop
		return json.dumps({
			'ret' : 0, 
			'data' : {
				'total'      : len(data), 
				'page_size'  : int(param.page_size),
				'page_index' : int(param.page_index),
				'skus'       : data,
			}
		})
