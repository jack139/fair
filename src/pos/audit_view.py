#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/pos/audit_view')

# 查看盘点结果
class handler:        #class PosAuditView:
	def GET(self): # 计算盘点数据
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			render = helper.create_render()
			user_data=web.input(audit='', cat='2')

			if user_data.audit=='':
				return render.info('参数错误！')

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 是否还有未结束账期的
			db_audit = db.shop_audit.find_one({
				'_id' : ObjectId(user_data.audit),
				'shop': db_shop['shop'], 
			})
			if db_audit==None:
				return render.info('未查到账期数据！')

			audit_stock = db_audit['stock'].copy()

			skus = []
			for i in audit_stock.keys():
				skus.append(audit_stock[i]['sku'])
			#print skus

			# 取得sku信息
			db_sku = db.sku_store.find({'_id':{'$in':skus}},
				{'unit':1, 'base_sku':1})
			tmp_sku = {}
			for i in db_sku:
				base_sku=db.dereference(i['base_sku'])
				tmp_sku[i['_id']]=(base_sku['name'], helper.UNIT_TYPE[i['unit']])
			#print tmp_sku

			if user_data.cat=='1':
				return render.pos_audit_commit(helper.get_session_uname(), helper.get_privilege_name(), 
					(db_audit['begin_date'],db_audit['end_date']), audit_stock, tmp_sku, 
					(db_audit['revenue'],db_audit['cost'],db_audit['gross'],db_audit['loss']))
			else:
				return render.pos_audit_commit2(helper.get_session_uname(), helper.get_privilege_name(), 
					(db_audit['begin_date'],db_audit['end_date']), audit_stock, tmp_sku, 
					(db_audit['revenue'],db_audit['cost'],db_audit['gross'],db_audit['loss']))
		else:
			raise web.seeother('/')
