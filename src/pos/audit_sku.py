#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, re
from config import setting
import helper

db = setting.db_web

url = ('/pos/audit_sku')

# 店内盘点－sku盘点操作
class handler:        #class PosAuditSku:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			render = helper.create_render()
			user_data=web.input(is_pack='k')

			is_pack = user_data['is_pack']

			# 分3类： u－散称sku， k－包装sku，w-已称重sku
			if is_pack not in ('k', 'u', 'w'):
				return render.info('错误的参数！')

			# 查找
			db_shop = helper.get_shop_by_uid()
			# 查找店面信息
			db_shop2 = helper.get_shop(db_shop['shop'])
			if db_shop2==None:
				return render.info('未找到所属门店！')
			
			# 查找所属店铺库存 包装库存
			# 模糊查询，以k开头 {'$regex':'k.*','$options': 'i'}
			condition = {
				'shop'       : db_shop['shop'],
				'product_id' : { '$not': re.compile('^w.*') },
			}
			# 称重sku忽略已售出的 num==0
			if is_pack=='w':
				condition['product_id'] = { '$regex' : 'w.*', '$options' : 'i' }
				condition['num']={'$ne':0}
			# 查询db
			db_invent = db.inventory.find(condition, {
				'sku'        : 1, 
				'online'     : 1, 
				'price'      : 1, 
				'weight'     : 1, 
				'total'      : 1, 
				'product_id' : 1, 
				'num'        : 1,
				'audit'      : 1,
			}).sort([('product_id',1)])

			invent = []
			skus = []
			for s in db_invent:
				skus.append(s['sku'])
				invent.append((
					s['sku'],  #0
					s['online'],   #1
					s['price'],   #2
					s['weight'],  #3
					s['total'] if s.has_key('total') else '',   #4
					s['product_id'], #5
					s['num'], #6
					s['audit'], #7
				))  

			# 包装的、有效的sku
			db_sku=db.sku_store.find({'_id':{'$in':skus}} ,{
				'product_id' : 1,
				'base_sku'   : 1,
				#'note'       : 1,
				#'online'     : 1,
				'is_pack'    : 1,
				'unit'       : 1,
				'app_title'  : 1,
				#'unit_num'   : 1,
				'ref_price'  : 1,
			}).sort([('_id',1)])

			skus = {}
			for u in db_sku:
				base_sku = db.dereference(u['base_sku'])

				skus[u['_id']]=(
					base_sku['name'] if len(u['app_title'].strip())==0 else u['app_title'],   #8
					'',  #9
					helper.UNIT_TYPE[u['unit']],   #10
					u['is_pack'],   #11
					u['ref_price'],   #12
				)

			data = []
			for i in invent:
				# 准备数据
				data.append(i + skus[i[0]])

			return render.pos_audit_sku(helper.get_session_uname(), helper.get_privilege_name(), data,
				 (str(db_shop2['_id']), db_shop2['name'], helper.SHOP_TYPE[db_shop2['type']]),
				 is_pack)
		else:
			raise web.seeother('/')

	def POST(self): # 修改盘点数量，json 返回
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			user_data=web.input(product_id='', audit_num='') # 

			if user_data.product_id=='':
				return json.dumps({'ret' : -1, 'msg' : '参数错误'})

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			if user_data.product_id[0]!='w' and user_data.product_id[2]=='2':  # 称重sku，可能会是浮点数
				audit_num = float(user_data.audit_num)
			else:
				audit_num = int(user_data.audit_num)
			r = db.inventory.update_one(
				{
					'product_id'  : user_data.product_id,
					'shop'        : db_shop['shop'],
				},
				{ 
					'$set'  : { 'audit' : audit_num},
					'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
						'记录盘点数量为 %.2f' % float(audit_num))},
				}
			)
			if r.matched_count>0:
				return json.dumps({'ret' : 0, 'num' : audit_num})
			else:
				return json.dumps({'ret' : -1, 'msg' : '未找到库存数据！'})
		else:
			return json.dumps({'ret' : -3, 'msg' : '无权限访问'})
