#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/pt_sku_list')

# 查询商品，允许分段查询返回
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', region_id='')

		if param.region_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#if not (param.page_size.isdigit() and param.page_index.isdigit()): 
		#	return json.dumps({'ret' : -3, 'msg' : 'page参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			# 区别首单用户
			#ccc = db.order_app.find({'user':{'$in':uname.values()}, 
			#	'status':{'$nin':['DUE','TIMEOUT','CANCEL']}},{'_id':1}).count()

			now_tick = int(time.time())

			# 查找拼团商品信息清单
			condition = {
				'region_id'   : { '$in' : [ param.region_id ] },
				'online'      : { '$in' : [ param.region_id ] },
				'expire_tick' : { '$gt' : now_tick } # 过期隐藏
			}
			#if ccc > 0: # 非首单，要回避只首单可见的商品 2015-09-25
			#	condition['first_order'] = { '$ne' : 1 }

			# 取所有商品数据 
			db_invent = db.pt_store.find(condition).sort([('sort_weight',1), ('_id',-1)])

			# 售罄的沉底
			db_invent2 = []
			db_num_0 = []
			for s in db_invent:
				if s['sale_out']!=1:
					db_invent2.append(s)
				else:
					db_num_0.append(s)
			db_invent2.extend(db_num_0)

			# 取指定区间的 2015-10-29
			#start_pos = int(param.page_size)*int(param.page_index)
			#end_pos = start_pos + int(param.page_size)
			#db_invent3 = db_invent2[start_pos:end_pos]

			image_host = 'http://%s/image/product' % setting.image_host

			data = []
			for i in db_invent2:
				# 准备数据
				new_one = {
					'tuan_id'     : i['tuan_id'], 
					'title'       : i['title'],
					'desc'        : i['desc'],   
					'price'       : i['price'],       
					'tuan_price'  : i['tuan_price'],  
					'ref_price'   : i['ref_price'],   
					'volume'      : '%d件' % i['volume'],
					'promote'     : True if i['promote']==1 else False,
					'promote_img' : '%s/images/promote.png' % image_host,
					'image'       : ['%s/%s/%s' % (image_host, x[:2], x) for x in i['image']],
					'tuan_size'   : i['tuan_size'],   
					'sale_out'    : True if i['sale_out']==1 else False,
					'expired'     : True if i['expire_tick']<now_tick else False,
				}

				# 设置标签 2015-09-27
				if new_one['promote']>0:
					for j in app_helper.left_tag['tags']:
						if i['tuan_id'] in j['skus']:
							new_one['promote_img'] = image_host+j['tag']
							break

				data.append(new_one)

			#print data

			# 返回
			return json.dumps({
				'ret' : 0, 
				'data' : {
					'region_id' : param.region_id,
					'total'     : len(data), 
					'tuans'     : data,
				}
			})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
