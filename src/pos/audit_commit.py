#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, re
from config import setting
import helper

db = setting.db_web

url = ('/pos/audit_commit')

# 店内盘点，提交盘点结果
class handler:        #class PosAuditCommit:
	def GET(self): # 计算盘点数据
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			render = helper.create_render()
			user_data=web.input(cat='2')

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 是否还有未结束账期的
			db_audit = db.shop_audit.find_one({'shop':db_shop['shop'], 'status':'OPEN'})
			if db_audit==None:
				return render.info('未查到未结束的盘点账期数据！')

			# 盘点数据
			audit_stock = db_audit['stock'].copy()

			# 临时数据处理
			new_audit_stock={}
			for i in audit_stock.keys():
				if i[0]!='w':
					new_audit_stock[i]=audit_stock[i]
			#print new_audit_stock
			audit_stock = new_audit_stock

			# 取得库存数据、盘点纪录
			db_invent = db.inventory.find({
					'shop'       : db_shop['shop'],
					'product_id' : { '$not': re.compile('^w.*') } # 不盘点w-prod
				}, {
					'product_id'  : 1,
					'num'         : 1, 
					'weight'      : 1, 
					'sku'         : 1, 
					'audit'       : 1, 
					'cost_price'  : 1,
					#'ref_prod_id' : 1, # 只有 w-prod  有
					#'weight_time' : 1, # 只有 w-prod  有
				}
			).sort([('product_id',1)]) # 排序保证后处理 w-prod
			skus = []
			tmp_stock = []
			for i in db_invent:
				skus.append(i['sku'])
				tmp_stock.append((
					i['product_id'], 
					i['num'], 
					i['weight'], 
					i['audit'] if i['audit']>=0 else i['num'], # 未盘的用期末库存代替 
					i['sku'],
					i['cost_price'],
					#i['weight_time'] if i.has_key('weight_time') else '',
					#i['ref_prod_id'] if i.has_key('ref_prod_id') else ''
				))

			# 计算盘点结果
			total_cost = 0.0
			total_loss = 0.0
			for i in tmp_stock:
				# 期初数据
				if not audit_stock.has_key(i[0]):
					audit_stock[i[0]]={'begin' : ('0.00', 0)}

				# 统计收货数量
				'''
				if i[0][0]=='w': # 称重项目
					if i[5]!='' and i[5]>db_audit['begin_date']: # and i[5]<db_audit['end_date']:
						# 本账期内称重的
						audit_stock[i[0]]['receive'] = (audit_stock[i[6]]['receive'][0], 1)
					else:
						# 以前账期称重的
						if audit_stock[i[0]]['begin'][1]==0 and i[1]==0 and i[3] in (0, -1):
							# 期初期末都为0，盘点为0或未盘，是过往已销售项目，不计入本期盘点
							audit_stock.pop(i[0], None)
							continue
						else:
							# 期初或期末不为0, 需要计入盘点
							audit_stock[i[0]]['receive'] = (audit_stock[i[6]]['receive'][0], 0)
				else:
				'''
				db_receive = db.order_stock.find({
					'type'         : 'SEND',
					'status'       : {'$in' : ['CONFIRM', 'FINISH']},
					'shop_to'      : db_shop['shop'],
					'product_id'   : i[0],
					'confirm_time' : {'$gt':db_audit['begin_date']},
					#'confirm_time' : {'$lt':db_audit['end_date']},
				}, {'cost_price':1, 'num':1})
				total_price = 0.0
				total_num =0.0
				for j in db_receive:
					total_price += float(j['cost_price'])*j['num']
					total_num += j['num']
				# 纪录平均价格（加权平均）
				if total_num>0:
					avg_price = round(total_price / total_num, 2)
					audit_stock[i[0]]['receive'] = ('%.2f' % avg_price, total_num)
				else:
					audit_stock[i[0]]['receive'] = ('0.00', 0)

				#对 u-prod 要减去称重的数量
				'''
				if i[0][0]=='u':
					# 查找sku同源的 w-prod, 在本账期内
					db_weight=db.inventory.find({
						'shop'        : db_shop['shop'],
						'product_id'  : { '$regex' : 'w.*', '$options' : 'i' },
						'sku'         : i[4],
						'weight_time' : {'$gt':db_audit['begin_date']},
						#'weight_time' : {'$lt':db_audit['end_date']},
					}, {'weight':1})
					total_weight = 0.0
					for j in db_weight:
						total_weight += float(j['weight'])
					audit_stock[i[0]]['weight'] = '%.2f' % -round(total_weight, 2)
				elif i[0][0]=='w':
					#对 w-prod 称重的数量为实际重量
					audit_stock[i[0]]['weight'] = i[2]
				else:
					audit_stock[i[0]]['weight'] = '0.00'
				'''

				# 期末数据
				'''
				if i[0][0]=='w':
					# w-prod 均价数据来自对应 u-prod
					audit_stock[i[0]]['end'] = (audit_stock[i[6]]['end'][0], i[1])
					audit_stock[i[0]]['audit'] = (audit_stock[i[6]]['audit'][0], i[3])
				else:
					# 计算期末平均价格
					avg_price = 0.0
					sum_begin = float(audit_stock[i[0]]['begin'][0])*audit_stock[i[0]]['begin'][1]
					sum_recei = float(audit_stock[i[0]]['receive'][0])*audit_stock[i[0]]['receive'][1]
					sum_num = audit_stock[i[0]]['begin'][1]+audit_stock[i[0]]['receive'][1]
					if sum_num>0:
						avg_price = round((sum_begin+sum_recei) / sum_num, 2)
					# 期末数据
					audit_stock[i[0]]['end'] = ('%.2f' % avg_price, i[1])
					audit_stock[i[0]]['audit'] = ('%.2f' % avg_price, i[3])
				'''
				# 期末数据
				audit_stock[i[0]]['end'] = (i[5], i[1])
				audit_stock[i[0]]['audit'] = (i[5], i[3])

				# 计算盘点结果：损耗
				#      盘点 － 期末 ＝ 损耗
				loss = audit_stock[i[0]]['audit'][1] - audit_stock[i[0]]['end'][1] 
				loss_cost = loss * float(audit_stock[i[0]]['audit'][0])
				audit_stock[i[0]]['loss'] = ('%.2f' % round(loss_cost, 2), loss)

				#   销售成本：(期初+进货-期末)*avg_price
				sale_num = audit_stock[i[0]]['begin'][1] + \
					audit_stock[i[0]]['receive'][1] - \
					audit_stock[i[0]]['end'][1]
				#if i[0][0]=='u': # 对 u-prod 还要减去 称重数量
				#	sale_num += float(audit_stock[i[0]]['weight'])
				#if i[0][0]=='w': 
				#	# w-prod 的成本根据沉重数量计算, 正常 sale_num==1, ==0说明没销售
				#	sale_cost = sale_num * float(audit_stock[i[0]]['weight']) * float(audit_stock[i[0]]['end'][0])
				#else:
				#	sale_cost = sale_num * float(audit_stock[i[0]]['end'][0])
				audit_stock[i[0]]['sale'] = ['0.00', 0, round(sale_num, 2)]

				# 累计所有成本（金额）
				#total_cost += sale_cost
				# 累计所有损耗（金额）
				total_loss += loss_cost

				# 记录sku，方便后续查询，冗余数据
				audit_stock[i[0]]['sku'] = i[4]


			# 统计销售额 revenue, 各porduct_id的销售量，成本
			db_sold = db.order_offline.find({
				'shop'      : db_shop['shop'],
				'status'    : 'PAID',
				'paid_time' : {'$gt':db_audit['begin_date']},
			}, {'due':1, 'cart':1, 'cost':1})
			revenue = 0.0
			total_cost = 0.0
			for j in db_sold:
				revenue += float(j['due'])  # 累计销售额
				total_cost += float(j['cost']) # 累计销售成本
				for k in j['cart']: # 累计各product_id的销量，和成本
					#if k['product_id'][0]=='w': # 对w-prod，计入对应的u-prod
					#	audit_stock[k['ref_prod_id']]['sale'][0] = '%.2f' % \
					#		(float(audit_stock[k['ref_prod_id']]['sale'][0])+float(k['cost']))
					#	audit_stock[k['ref_prod_id']]['sale'][1] += float(k['num'])
					#else:
					audit_stock[k['product_id']]['sale'][0] = '%.2f' % \
						(float(audit_stock[k['product_id']]['sale'][0])+float(k['cost']))
					audit_stock[k['product_id']]['sale'][1] += float(k['num'])
			# 总销售收入
			revenue_s = '%.2f' % round(revenue, 2)
			# 毛利额：销售收入 － 销售成本
			gross = revenue - total_cost
			gross_s = '%.2f' % round(gross, 2)
			# 总销售成本
			total_cost_s = '%.2f' % round(total_cost, 2)
			# 总耗损
			total_loss_s = '%.2f' % round(total_loss, 2)

			# 结束，保存到db
			db.shop_audit.update_one({'_id':db_audit['_id']}, {'$set' : {
				'stock'   : audit_stock,
				'revenue' : revenue_s,
				'cost'    : total_cost_s,
				'gross'   : gross_s,
				'loss'    : total_loss_s,
			}})

			# 取得sku信息
			db_sku = db.sku_store.find({'_id':{'$in':skus}},
				{'unit':1, 'base_sku':1})
			tmp_sku = {}
			for i in db_sku:
				base_sku=db.dereference(i['base_sku'])
				tmp_sku[i['_id']]=(base_sku['name'], helper.UNIT_TYPE[i['unit']])

			if user_data.cat=='1':
				return render.pos_audit_commit(helper.get_session_uname(), helper.get_privilege_name(), 
					(db_audit['begin_date'],''), audit_stock, tmp_sku, 
					(revenue_s,total_cost_s,gross_s,total_loss_s), False)
			else:
				return render.pos_audit_commit2(helper.get_session_uname(), helper.get_privilege_name(), 
					(db_audit['begin_date'],''), audit_stock, tmp_sku, 
					(revenue_s,total_cost_s,gross_s,total_loss_s), False)
		else:
			raise web.seeother('/')

	def POST(self): # 结束账期
		if helper.logged(helper.PRIV_USER,'POS_AUDIT'):
			render = helper.create_render()

			# 查找shop
			db_shop = helper.get_shop_by_uid()

			# 是否还有未结束账期的
			db_audit = db.shop_audit.find_one({'shop':db_shop['shop'], 'status':'OPEN'},
				{'_id':1, 'stock':1})
			if db_audit==None:
				return render.info('没有未结束的盘点账期！')

			audit_stock = db_audit['stock'].copy()

			for i in audit_stock.keys():
				r = db.inventory.update_one(
					{
						'product_id'  : i,
						'shop'        : db_shop['shop'],
					},
					{ 
						'$set'  : { 'num' : audit_stock[i]['audit'][1], 'audit' : -1},
						'$push' : { 'history' : (helper.time_str(), helper.get_session_uname(), 
							'库存数量 %.2f 修改为盘点数量 %.2f' % \
							(float(audit_stock[i]['end'][1]),float(audit_stock[i]['audit'][1])))
						},
					}
				)
				if r.matched_count==0:
					return render.info('未找到库存记录 %s！' % i)

				# 更新第3方库存 2015-10-10
				helper.elm_modify_num(db_shop['shop'], i)


			# 删除所有称重项目
			db.inventory.remove({
				'shop'        : db_shop['shop'],
				'product_id'  : { '$regex' : 'w.*', '$options' : 'i' },
				#'num'         : { '$gt' : 0 },
			})

			# 结束账期
			db.shop_audit.update_one({'_id':db_audit['_id']},{'$set':{
				'shop'     : db_shop['shop'],
				'end_date' : helper.time_str(),
				'status'   : 'CLOSE'
			}})

			return render.info('账期已关闭！','/pos/audit')
