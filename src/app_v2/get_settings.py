#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v2|v3)/get_settings')

# 获取全局参数
class handler:        
	def POST(self, version='v2'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', secret='', sign='')

		if '' in (param.app_id, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

		# 返回全局参数
		ret_data = {'ret' : 0, 'data' : {
			'delivery_fee'  : '%.2f' % app_helper.delivery_fee,
			'free_delivery' : '%.2f' % app_helper.free_delivery,
			'first_promote' : '%.2f' % app_helper.first_promote,
			'image_host2'   : 'http://%s/image/product' % setting.image_host,
			'notify_host'   : 'http://%s' % setting.notify_host,
			#'notify_host'   : 'http://app.urfresh.cn', 
			'cod_enable'    : app_helper.cod_enable,
			'alipay_enable' : app_helper.alipay_enable,
			'wxpay_enable'  : True, #app_helper.wxpay_enable,
			'credit_enable' : app_helper.credit_enable,
			'category'      : app_helper.CATEGORY2,
			'banner'        : app_helper.BANNER,
			'banner_url'    : app_helper.BANNER_URL,
			'default_shop'  : setting.default_shop, # 返回默认站店
			'default_name'  : db_shop['name'] if db_shop else '',
			'alert'         : app_helper.start_alert, # 多余
			'message'       : app_helper.start_message, # ios使用
			'message2'       : app_helper.start_message, # 安卓使用
		}}
		if version=='v3':
			ret_data['data']['wxpay_enable']=True #app_helper.wxpay_enable
			ret_data['data']['credit_enable']=True #app_helper.credit_enable
			ret_data['data']['release_date']='20151020'
			ret_data['data']['release_date2']='20151027'
			ret_data['data']['apk_url']=''
			ret_data['data']['wxpay_enable2']=True #app_helper.wxpay_enable
			ret_data['data']['credit_enable2']=True #app_helper.credit_enable

		#print ret_data

		return json.dumps(ret_data)
		