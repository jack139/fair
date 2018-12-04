#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from config import setting
import helper

db = setting.db_web

url = ('/pos/audit')

# 店内盘点－盘点纪录
class handler:        #class PosAudit:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			render = helper.create_render()
			# 查找shop
			db_shop = helper.get_shop_by_uid()

			db_audit = db.shop_audit.find({'shop': db_shop['shop']}).sort([('_id',-1)])

			return render.pos_audit(helper.get_session_uname(), helper.get_privilege_name(), db_audit)
		else:
			raise web.seeother('/')

	def POST(self): # 新账期，json 返回
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			user_data=web.input(cate='') # 2- 当前时间开始， 1 － 接最近一个结束账期

			if user_data.cate=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 是否还有未结束账期的
			db_audit = db.shop_audit.find_one({'shop':db_shop['shop'], 'status':'OPEN'},{'_id':1})
			if db_audit:
				return json.dumps({'ret' : -1, 'msg' : '尚有未结束的账期！'})

			begin_date = helper.time_str()
			begin_stock = []
			if user_data.cate=='1': 
				# 接上一个账期，用最近一个账期数据做期初数据
				db_audit = db.shop_audit.find({'shop':db_shop['shop'], 'status':'CLOSE'},
					{'end_date':1, 'stock':1}).sort([('end_date',-1)])
				if db_audit.count()==0:
					#return json.dumps({'ret' : -1, 'msg' : '未找到最近的盘点数据！'})

					# 当前时间开始账期，用当前库存做期初数据
					db_invent = db.inventory.find({
						'shop':db_shop['shop'],
						'num' : {'$gt' : 0},
					}, {'product_id':1, 'num':1, 'sku':1, 'weight':1})
					#print db_invent.count()
					skus = []
					tmp_stock = []
					for i in db_invent:
						tmp_stock.append((i['product_id'], i['num'], i['weight'], i['sku']))
						skus.append(i['sku'])

					# 找参考成本价，使用sku的参考成本
					tmp_price = {}
					db_sku = db.sku_store.find({'_id' : {'$in' : skus}}, {'ref_price':1})
					for i in db_sku:
						tmp_price[i['_id']]=i['ref_price']

					begin_stock = {}
					for i in tmp_stock:
						begin_stock[i[0]]={
							'begin' : (tmp_price[i[3]], i[1]),
						}
				else:
					begin_date = db_audit[0]['end_date']
					# 将最近一次盘点数据作为新的期初数据
					# {
					#	'k00001' : { 
					#		'begin'   : (<ref_price>, <num>),
					#		'end'     : (<ref_price>, <num>),
					#		'audit'   : (<ref_price>, <num>),
					#		'receive' : (<ref_price>, <num>), 
					#		'weight'  : (<ref_price>, <num>), # 只有 u-prod 有意义
					#	}
					#}
					begin_stock = {}
					for i in db_audit[0]['stock'].keys():
						begin_stock[i] = {'begin' : db_audit[0]['stock'][i]['audit']}
			else:
				# 当前时间开始账期，用当前库存做期初数据
				db_invent = db.inventory.find({
					'shop':db_shop['shop'],
					'num' : {'$gt' : 0},
				}, {'product_id':1, 'num':1, 'sku':1, 'weight':1})
				#print db_invent.count()
				skus = []
				tmp_stock = []
				for i in db_invent:
					if i['product_id'][0]=='w':
						continue
					tmp_stock.append((i['product_id'], i['num'], i['weight'], i['sku']))
					skus.append(i['sku'])

				# 找参考成本价，使用sku的参考成本
				tmp_price = {}
				db_sku = db.sku_store.find({'_id' : {'$in' : skus}}, {'ref_price':1})
				for i in db_sku:
					tmp_price[i['_id']]=i['ref_price']

				begin_stock = {}
				for i in tmp_stock:
					begin_stock[i[0]]={
						'begin' : (tmp_price[i[3]], i[1]),
					}

			# 添加新账期
			db.shop_audit.insert({
				'shop'       : db_shop['shop'],
				'status'     : 'OPEN',
				'begin_date' : begin_date,
				'end_date'   : '',
				'stock'      : begin_stock,
			})

			# 初始化sku盘点数据，-1表示为未盘点
			db.inventory.update_many({'shop':db_shop['shop']},{'$set':{'audit':-1}})

			return json.dumps({'ret' : 0, 'msg' : '操作完成'})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
