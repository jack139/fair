#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/stock/inventory_json')

# 返回指定sku的所有站点库存
class handler:        #class StockInventoryJson: 
	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'STOCK_INVENTORY'):
			user_data=web.input(sku='')

			if user_data.sku=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			db_invent=db.inventory.find({'sku':ObjectId(user_data['sku'])},
				{'shop':1,'num':1,'product_id':1,'weight':1,'history':1}
			).sort([('product_id',1)]) # 排序让w在最后, 如果u和w并存

			# 收集站点
			data={}
			shops=[]
			product_id=''
			for i in db_invent:
				# 对称重sku，要将已称重的库存加到未称重的库存中
				if data.has_key(str(i['shop'])): # 应该是w，因为u在w之前已经添加相同shop信息
					data[str(i['shop'])]['num'] = float(data[str(i['shop'])]['num'])+float(i['weight'])
				else:
					shops.append(i['shop'])
					product_id=i['product_id']
					data[str(i['shop'])]={
						'shop'       : str(i['shop']),
						'num'        : i['num'],
						'num_change' : 0,
						'history'    : i['history'],
					}
			
			# 查询站点的 送货单(包括仓库预计出货，店面预计收货)
			db_send = db.order_stock.find({
				'type'       : 'SEND',
				'status'     : {'$nin': ['CONFIRM', 'FINISH']}, 
				'product_id' : product_id,
				'$or': [
					{'shop_from' : {'$in' : shops}},
					{'shop_to'   : {'$in' : shops}}
				]},  {'shop_from' : 1, 'shop_to' : 1, 'num' : 1, 'num_onroad':1}
			)

			for i in db_send:
				if str(i['shop_from']) in data:
					data[str(i['shop_from'])]['num_change'] += i['num_onroad']-i['num']
				if str(i['shop_to']) in data:
					data[str(i['shop_to'])]['num_change'] += i['num']

			return json.dumps({'ret': 0, 'data':data})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
