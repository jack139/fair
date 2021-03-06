#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/sku_detail')

# 查询商品详情
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', shop_id='', product_id='', session='', sign='')

		if '' in (param.app_id, param.shop_id, param.product_id, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		print param
		
		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.session, param.shop_id, param.product_id])
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
			'maximun'       : 1,
			'volume'        : 1,
		})

		base_sku = db.dereference(db_sku['base_sku'])

		# 处理整箱预售
		if db_sku['list_in_app']== -3: # 关闭整箱预售 2015-10-27 
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

		if db_invent==None:
			return json.dumps({'ret' : -2, 'msg' : '参数错误: 商品代码错误'})

		print db_invent

		# 调整价格显示，有分的金额才显示2位小数， 2015-10-30
		if ('%.2f'%float(db_invent['price']))[-1]=='0':
			show_price = '%.1f' % float(db_invent['price'])
		else:
			show_price = '%.2f' % float(db_invent['price'])

		# 准备返回结果
		data = {
			'product_id' : db_invent['product_id'],
			'title'      : db_sku['app_title'],
			'abstract'   : base_sku['abstract'],
			'price'      : show_price,
			'num'        : max(int(db_invent['num']),0),
			'promote'    : db_sku['promote'],
			'promote_img': app_helper.left_tag['default2'],
			'detail_url' : '',
			'volume'     : '%d件' % int(db_sku.get('volume', 0)), # 销量，需要后台实现
			'max_can_buy': max(int(db_invent['num']),0) if int(db_sku['maximun'])==0 else int(db_sku['maximun']),
			'message'    : '' if int(db_sku['maximun'])==0 else '该商品每单限购%d件' % int(db_sku['maximun'])
		}

		# 是否有优惠价格
		if db_sku['is_onsale']==1 and float(db_sku['special_price'])<float(db_invent['price']): 
			# 优惠价格比门店价格低
			# 调整价格显示，有分的金额才显示2位小数， 2015-10-30
			if ('%.2f'%float(db_sku['special_price']))[-1]=='0':
				data['sale_price']='%.1f' % float(db_sku['special_price'])
			else:
				data['sale_price']='%.2f' % float(db_sku['special_price'])

		# 图片
		if base_sku.has_key('image'):
			#if len(base_sku['image'])>1:
			#	i = base_sku['image'][1] # 第2张是详情图
			#else:
			#	i = base_sku['image'][0] 
			#data['image']=['/%s/%s' % (i[:2], i)]	
			data['image']=['/%s/%s' % (i[:2], i) for i in base_sku['image']]
			if len(data['image'])>1: # 如果不止一张图，第2张开始时详情图
				data['image'].pop(0) # 把第1张去除
		else:
			data['image']=''

		# 设置标签 2015-09-27
		if data['promote']>0:
			for j in app_helper.left_tag['tags']:
				if db_invent['product_id'] in j['skus']:
					data['promote_img'] = j['tag']
					break

		if version=='v3':
			data['max_can_buy'] = int(db_sku['maximun']) # 0 表示不限购
			# 设置买X送Y
			if db_invent['product_id'] in app_helper.buy_X_give_Y.keys():
				data['xx'] = app_helper.buy_X_give_Y[db_invent['product_id']][0] 
				data['yy'] = app_helper.buy_X_give_Y[db_invent['product_id']][1]
			else:
				data['xx'] = 100000
				data['yy'] = 0

			data['only_one'] = app_helper.only_one
			data['only_one_message'] = '每单只能购买1种该促销活动商品'

		#print data

		# 返回
		return json.dumps({
			'ret' : 0, 
			'data' : data
		})
