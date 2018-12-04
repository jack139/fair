#!/usr/bin/env python
# -*- coding: utf-8 -*-

from config import setting
import gc,sys
import  time, json
import app_helper, elm_helper

db = setting.db_web
db_rep = app_helper.db_rep

global null
null = 'None'

DEALY=15

def modify_stock_info(food_id,stock,title):
	restaurant_info_path_url = "/food/{0}/".format(food_id)
	method = 'PUT'
	params = {}
	params['stock'] = max(int(stock),0)
	if len(title)>0:
		params['name'] = title
	
	elm_helper.elm_port(restaurant_info_path_url,params,method)

def get_weight(sort_weight):
	s = 1000-sort_weight
	if s < 0 or s == 0:
		s = 0
	else:
		s
	return s

def modify_inventory():
	#修改库存
	#print 'modify_inventory()'
	'''查询数据库中的所有数据'''
	inv_modify_db = db_rep.inv_modify.find(limit=1).sort([('_id',1)])
	if inv_modify_db.count()>0: # 有更新的
		i = inv_modify_db[0]
		'''根据shop_id和product_id查询food_id'''
		product_category_db = db_rep.product_category.find_one({'shop':i['shop_id'],'product_id':i['product_id']},{'elm_food_id':1})
		if product_category_db:
			'''根据查询的值修改库存'''
			# 应该作失败检查！！！
			modify_stock_info(product_category_db['elm_food_id'],max(i['num'],0),i.get('title','')) # 负库存填零
			print '更新elm库存: ',i['shop_id'],i['product_id'],i['num'],i.get('title','n/a').encode('utf-8')
			'''根据id删除'''
			db_rep.inv_modify.delete_one({'_id':i['_id']})
		else:
			print '新商品上架' 
			'''根据shop_id查询restaurant_id'''
			shop_restaurant = db_rep.shop_restaurant.find_one({'shop_id':i['shop_id']},{'elm_restaurant_id':1})
			if shop_restaurant==None: # 未知店铺，删除更新信息
				print '未知店铺：',i['shop_id']
				db_rep.inv_modify.delete_one({'_id':i['_id']})
				return

			'''根据shop_id和product_id查询详细信息'''
			inventory_db = db.inventory.find_one({'shop':i['shop_id'],'product_id':i['product_id']},{'category':1,'sort_weight':1,'sku':1,'price':1,'num':1,'product_id':1})
			'''根据查询出的category_id查询product_category数据库中是否存在'''

			# 取得商品分类
			restaurant_info_path_url = '/restaurant/%d/food_categories/'%int(shop_restaurant['elm_restaurant_id'])
			r1 = elm_helper.elm_port(restaurant_info_path_url,{},'GET')
			r2 = json.loads(r1)
			if r2['code']!=200:
				print '获取分类失败'
				print r2
				db_rep.inv_modify.delete_one({'_id':i['_id']})
				return
			# 取第1个分类
			if len(r2['data']['food_categories']):
				print '取得分类：', r2['data']['food_categories'][0]['name'].encode('utf-8')
				elm_category_id = r2['data']['food_categories'][0]['food_category_id']
			else: # 没有分类
				print '新建食物分类'
				restaurant_info_path_url = "/food_category/"
				method = 'POST'
				params = {}
				params['restaurant_id'] = int(shop_restaurant['elm_restaurant_id'])
				params['name'] = app_helper.CATEGORY[inventory_db['category']]
				params['weight'] = int(get_weight(inventory_db['sort_weight']))
				print params
				response = elm_helper.elm_port(restaurant_info_path_url,params,method)
				print response
				category = json.loads(response)
				if category['code']!=200:
					print '新建食物分类 elm 报错！忽略此项：', i
					db_rep.inv_modify.delete_one({'_id':i['_id']})	 
					return				
				category_id = category['data']['food_category_id']
				print category['data']['food_category_id']
				elm_category_id = category_id

			'''添加食物'''
			restaurant_info_path_url_f = "/food/"
			method_f = 'POST'
			params_f = {}
			'''根据product_id查询商品详细信息'''
			sku_store_db = db.sku_store.find_one({'product_id':i['product_id']},{'app_title':1})
			if sku_store_db and sku_store_db.has_key('app_title') and len(sku_store_db['app_title'].strip())>0:
				params_f['food_category_id'] = elm_category_id
				params_f['name'] = sku_store_db['app_title']
				new_price = float(inventory_db['price'])*1.08 # 加 8%
				params_f['price'] = round(int(new_price*10+0.5)/10.0, 2) # 取整到角
				params_f['description'] = ''
				params_f['max_stock'] = 1000
				params_f['stock'] = int(inventory_db['num'])
				print params_f
				food_response = elm_helper.elm_port(restaurant_info_path_url_f,params_f,method_f)
				print food_response
				food = json.loads(food_response)

				if food['code']!=200:
					print '添加食物 elm 报错！忽略此项：', i
					db_rep.inv_modify.delete_one({'_id':i['_id']})	 
					return

				food_id = food['data']['food_id']
				db_rep.product_category.insert_one({'product_id':i['product_id'],'elm_food_id':food_id,'category':inventory_db['category'],'elm_category_id':elm_category_id,'shop':i['shop_id']})
			else:
				print '非app商品：',i['product_id']
				db_rep.inv_modify.delete_one({'_id':i['_id']})	 
				return
	else: # 无更新的，sleep
		print 'sleep', app_helper.time_str()
		time.sleep(DEALY)

		
if __name__=='__main__':
  
	print "DISPATCHER: %s started" % app_helper.time_str()

	gc.set_threshold(300,5,5)

	try:
		while 1:
			hh = time.localtime().tm_hour
			
			if hh>=7 and hh<23:
				print '修改库存: %s' % app_helper.time_str()
				modify_inventory()
				
			sys.stdout.flush()

			time.sleep(0.1)

	except KeyboardInterrupt:
		print
		print 'Ctrl-C!'

	print "DISPATCHER: %s exited" % app_helper.time_str()










