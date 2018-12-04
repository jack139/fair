#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.dbref import DBRef
from config import setting
import helper

db = setting.db_web

url = ('/stock/inventory')

# 仓储管理 之 库存管理 -------------------		
class handler:        #class StockInventory:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'STOCK_INVENTORY'):
			render = helper.create_render()
			return render.stock_invent(helper.get_session_uname(), helper.get_privilege_name())
		else:
		    raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'STOCK_INVENTORY'):
			render = helper.create_render()
			user_data=web.input(cat='',content='')

			if user_data.cat=='':
				return render.info('参数错误！')  

			skus=[]

			# 按sku id查, 或者条件为空的查询 查询所以sku
			if user_data['content'].strip()=='' or user_data['cat']=='product_id': 
				if user_data['content'].strip()=='':
					condition = {}
				else:
					condition = {'product_id':user_data['content'].strip()}
				db_sku=db.sku_store.find(condition,{
					'product_id' : 1,
					'base_sku'   : 1,
					'note'       : 1,
					'available'  : 1,
					'is_pack'    : 1,
					'unit'       : 1,
					#'unit_num'   : 1,
					'ref_price'  : 1,
					'app_title'  : 1,
				}).sort([('_id',1)])

				for u in db_sku:
					base_sku = db.dereference(u['base_sku'])

					# 准备数据
					sku_name = base_sku['name'] if len(u['app_title'].strip())==0 else u['app_title']
					skus.append((u['_id'], sku_name, u['note'], u['available'],
						base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
						'', helper.UNIT_TYPE[u['unit']], 
						u['is_pack'], u['ref_price'], u['product_id'], base_sku['original'],
						helper.get_inventory(u['_id'])
					))

			# 按 品名、产地 查
			elif user_data['cat'] in ('name', 'original'): 
				# 先查到base_sku				
				# 模糊查询 {'$regex':'.*小.*','$options': 'i'}
				condition = {'$regex' : u'.*%s.*' % user_data['content'].strip(),'$options': 'i'}
				db_base = db.base_sku.find({user_data['cat']:condition},{
					'name'     : 1,
					'image'    : 1,
					'original' : 1,
				})
				# 再查含有base_sku的sku
				base={}
				for k in db_base:
					base[DBRef('base_sku', k['_id'])] = (k['name'],k['image'],k['original'])

				db_sku=db.sku_store.find({'base_sku':base.key()},{
					'product_id' : 1,
					'base_sku'   : 1,
					'note'       : 1,
					'available'  : 1,
					'is_pack'    : 1,
					'unit'       : 1,
					#'unit_num'   : 1,
					'ref_price'  : 1,
				}).sort([('_id',1)])

				# 准备数据
				for u in db_sku:
					k = base[DBRef('base_sku', u['_id'])]
					skus.append((u['_id'], k['name'], u['note'], u['available'],
						k['image'][0] if k.has_key('image') and len(k['image'])>0 else '',
						'', helper.UNIT_TYPE[u['unit']], 
						u['is_pack'], u['ref_price'], u['product_id'], k['original'],
						helper.get_inventory(u['_id'])
					))

			# 按站点查询
			elif user_data['cat']=='shop':
				condition = {'$regex' : u'.*%s.*' % user_data['content'].strip(),'$options': 'i'}
				db_shop = db.base_shop.find({'name':condition},{'name':1})
				shops = {}
				for h in db_shop:
					shops[h['_id']]=h['name']

				db_invent = db.inventory.find({'shop':{'$in':shops.keys()}},{'sku':1, 'num':1})
				invent = {}
				for i in db_invent:
					print i
					if invent.has_key(i['sku']):
						invent[i['sku']] += i['num']
					else:
						invent[i['sku']]=i['num']

				db_sku=db.sku_store.find({'_id':{'$in':invent.keys()}},{
					'product_id' : 1,
					'base_sku'   : 1,
					'note'       : 1,
					'available'  : 1,
					'is_pack'    : 1,
					'unit'       : 1,
					#'unit_num'   : 1,
					'ref_price'  : 1,
				}).sort([('_id',1)])

				for u in db_sku:
					base_sku = db.dereference(u['base_sku'])

					# 准备数据
					skus.append((u['_id'], base_sku['name'], u['note'], u['available'],
						base_sku['image'][0] if base_sku.has_key('image') and len(base_sku['image'])>0 else '',
						'', helper.UNIT_TYPE[u['unit']], 
						u['is_pack'], u['ref_price'], u['product_id'], base_sku['original'],
						invent[u['_id']]
					))

			return render.stock_invent_sku(helper.get_session_uname(), helper.get_privilege_name(), skus)
		else:
			raise web.seeother('/')
