#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time,sys,datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

db = MongoClient('10.168.11.151')['fair_db']
db.authenticate('report','report')

db2 = MongoClient('10.168.11.151')['report_db']
db2.authenticate('owner','owner')


# 订货报表

def date_to_day(d):
	d0 = ['周日','周一','周二','周三','周四','周五','周六',]
	da = d.split('-')
	return d0[int(datetime.date(int(da[0]),int(da[1]),int(da[2])).strftime("%w"))]

if __name__ == "__main__":
	if len(sys.argv)<2:
		print "usage: python %s <date> [-no-print]" % sys.argv[0]
		sys.exit(2)

	if len(sys.argv)>2 and sys.argv[2]=='-no-print':
		NO_PRINT=True
	else:
		NO_PRINT=False

	shops={}
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}},{'name':1})
	for i in db_shop:
		shops[i['_id']]=i['name']

	# 起至时间
	begin_d = sys.argv[1]
	end_d = sys.argv[1]

	# 昨天
	start_tick = int(time.mktime(time.strptime(end_d,"%Y-%m-%d"))) - 3600*24*7
	begin_d = time.strftime("%Y-%m-%d", time.localtime(start_tick))

	#print begin_d

	# 生成每天时间
	d1 = begin_d.split('-')
	d2 = end_d.split('-')
	dt = datetime.date(int(d1[0]),int(d1[1]),int(d1[2]))
	end = datetime.date(int(d2[0]),int(d2[1]),int(d2[2]))
	step = datetime.timedelta(days=1)

	days = []
	while dt <= end:
		days.append(dt.strftime('%Y-%m-%d'))
		dt += step

	#print days


	# 初始化sku数据
	skus_all = {}
	db_sku = db.sku_store.find({},
		{'product_id':1, 'base_sku':1, 'app_title':1, 'special_price':1, 'is_onsale':1, 'available':1, 'ref_price':1})
	for i in db_sku:
		base_sku = db.dereference(i['base_sku'])
		skus_all[i['product_id']]=(
			base_sku['name'] if len(i['app_title'].strip())==0 else i['app_title'],
			i['special_price'] if i['is_onsale']==1 else '',
			i['available'],
			i['ref_price'],
			i['special_price']
		)

	# 只计算昨天和今天的销量
	for day in days[-2:]:
		begin_date = '%s 00:00:00' % day
		end_date = '%s 23:59:59' % day

		condition = {
			'type'   : {'$nin':['TUAN','SINGLE']},
			'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']},
			'$and'   : [{'paid_time' : {'$gt' : begin_date}},
				    {'paid_time' : {'$lt' : end_date}}],
		}

		db_sale2 = db.order_app.find(condition, 
			{'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1,'shop':1})

		skus = {}
		for i in db_sale2:
			for j in i['cart']:
				# 忽略售价小于参考售价，且不失促销价的销售
				if float(j['price']) < float(skus_all[j['product_id']][3]) and float(j['price'])!=float(skus_all[j['product_id']][4]):
					#print 'skip sale:',i['shop'],i['order_id'],j['product_id'],j['num2'],j.get('numyy','0')
					continue
				if skus.has_key((i['shop'],j['product_id'])):
					skus[(i['shop'],j['product_id'])]['online']['price'] += float(j['price'])
					skus[(i['shop'],j['product_id'])]['online']['num'] += (float(j['num2']) + float(j.get('numyy', '0')))
				else:
					skus[(i['shop'],j['product_id'])]={
						'online' : {
							#'cost'  : float(j['cost']),
							'price' : float(j['price']),
							'num'   : (float(j['num2']) + float(j.get('numyy', '0'))),
						},
						'name'  : j['title'],
					}
		#print skus

		# 保存到 report_db
		for i in skus.keys():
			db2.cg01.update_one({'shop':i[0],'product_id':i[1],'date':day}, {'$set':{
				'price' : skus[i]['online']['price'],
				'num'   : skus[i]['online']['num'],
			}}, upsert=True)

	if NO_PRINT: # 只更新销量数据，不输出
		print 'Done.'
		sys.exit(2)

	# 查询当前的库存信息，并输出
	print '门店,商品代码,状态,商品名,门店库存,门店售价,促销价,%s,%s,%s,%s,%s,%s,%s,%s,拉取时间' % \
		(date_to_day(days[7]),date_to_day(days[6]),date_to_day(days[5]),
		 date_to_day(days[4]),date_to_day(days[3]),date_to_day(days[2]),
		 date_to_day(days[1]),date_to_day(days[0]))


	# 按店拉数据
	now_time = time.ctime()
	for shop in shops.keys():
		db_invent = db.inventory.find({'shop':shop},{'product_id':1,'price':1,'num':1})

		for i in db_invent:
			if i['product_id'][0]=='w' or i['product_id'][2]=='2': #忽略称重项目
				continue
			data_item = {
				'shop_name' : shops[shop],
				'product_id' : i['product_id'],
				'available':'停用' if skus_all[i['product_id']][2]==0 else '',
				'title' : skus_all[i['product_id']][0],
				'num' : i['num'],
				'price' : i['price'],
				'sale_price' : skus_all[i['product_id']][1],
				days[0]: 0,
				days[1]: 0,
				days[2]: 0,
				days[3]: 0,
				days[4]: 0,
				days[5]: 0,
				days[6]: 0,
				days[7]: 0,
				'now_time' : now_time,
			}

			# 索引 db.cg01.createIndex({shop:1,product_id:1,date:1})
			db_cg = db2.cg01.find({'shop': shop, 'product_id': i['product_id'], 'date':{'$in':days}})
			for i in db_cg:
				data_item[i['date']] = i['num']

			print \
				data_item['shop_name'].encode('utf-8')+','+ \
				data_item['product_id'].encode('utf-8')+','+ \
				data_item['available']+','+ \
				data_item['title'].encode('utf-8')+','+ \
				'%d' % data_item['num']+','+ \
				data_item['price'].encode('utf-8')+','+ \
				data_item['sale_price'].encode('utf-8')+','+ \
				'%d' % data_item[days[7]]+','+ \
				'%d' % data_item[days[6]]+','+ \
				'%d' % data_item[days[5]]+','+ \
				'%d' % data_item[days[4]]+','+ \
				'%d' % data_item[days[3]]+','+ \
				'%d' % data_item[days[2]]+','+ \
				'%d' % data_item[days[1]]+','+ \
				'%d' % data_item[days[0]]+','+ \
				data_item['now_time']

