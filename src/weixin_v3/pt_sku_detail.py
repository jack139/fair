#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/pt_sku_detail')

# 拼团活动详情
class handler:        
	def POST(self):
		web.header('Content-Type', 'application/json')
		param = web.input(openid='', session_id='', region_id='', tuan_id='', pt_order_id='')

		if '' in (param.region_id, param.tuan_id):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			now_tick = int(time.time())

			# 有效的tuan
			db_sku=db.pt_store.find_one({
				'tuan_id'     : param.tuan_id,
				'region_id'   : { '$in' : [ param.region_id ] },
				#'online'      : { '$in' : [ param.region_id ] },
				#'expire_tick' : { '$gt' : now_tick } # 过期不能查看
			})
			if db_sku==None:
				return json.dumps({'ret' : -2, 'msg' : 'tuan_id错误'})

			image_host = 'http://%s/image/product' % setting.image_host

			# 准备返回结果
			data = {
				'region_id' : param.region_id, 
				'tuan_id'     : db_sku['tuan_id'], 
				'title'       : db_sku['title'],
				'desc'        : db_sku['desc'],   
				'price'       : db_sku['price'],       
				'tuan_price'  : db_sku['tuan_price'],  
				'ref_price'   : db_sku['ref_price'],   
				'volume'      : '%d件' % db_sku['volume'],
				'promote'     : True if db_sku['promote']==1 else False,
				'promote_img' : '%s/images/promote.png'%image_host,
				'image'       : ['%s/%s/%s' % (image_host, x[:2], x) for x in db_sku['image']],
				'tuan_size'   : db_sku['tuan_size'],   
				'sale_out'    : True if db_sku['sale_out']==1 else False,
				'expired'     : True if db_sku['expire_tick']<now_tick else False,
				'pt_order_id' : param.pt_order_id,
				'status'      : '',
				'position'    : 'VISITOR', # 缺省为游客
			}

			# 已下架，显示售罄
			if param.region_id not in db_sku['online']:
				data['sale_out'] = True

			# 过期也显示售罄
			if data['expired']:
				data['sale_out'] = True

			# 图片
			#if base_sku.has_key('image'):
			#	data['image']=['/%s/%s' % (i[:2], i) for i in base_sku['image']]
			#	if len(data['image'])>1: # 如果不止一张图，第2张开始时详情图
			#		data['image'].pop(0) # 把第1张去除
			#else:
			#	data['image']=''

			# 设置标签 2015-09-27
			if data['promote']>0:
				for j in app_helper.left_tag['tags']:
					if db_sku['tuan_id'] in j['skus']:
						data['promote_img'] = image_host+j['tag']
						break

			if len(param.pt_order_id)>0: # 存在pt_order_id
				db_order = db.pt_order.find_one({'pt_order_id':param.pt_order_id})
				if db_order:
					data['status'] = db_order['status'] # 返回订单状态
					if db_order['status']=='OPEN':
						# 如果拼团中，按实际情况显示售罄，忽略下架
						data['sale_out'] = True if db_sku['sale_out']==1 else False

					for i in db_order['member']: # 查找是否已参团
						if i['openid']==uname['openid']:
							data['position'] = i['position']
							break

			# 返回
			#print data

			return json.dumps({'ret' : 0, 'data' : data})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})
