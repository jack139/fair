#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

urls = [
	'/wx/',			'First',
	'/wx/init_fair',	'InitFair',
	'/wx/fair',		'Fair',
	'/wx/init_my_order',	'InitMyOrder',
	'/wx/my_order',		'MyOrder',
	'/wx/init_my_coupon',	'InitMyCoupon',
	'/wx/my_coupon',	'MyCoupon',
	'/wx/init_my_credit',	'InitMyCredit',
	'/wx/my_credit',	'MyCredit',
	'/wx/init_my_bind',	'InitMyBind',
	'/wx/my_bind',		'MyBind',
	'/wx/init_my_address',	'InitMyAddr',
	'/wx/my_address',	'MyAddr',
	'/wx/init_tuan',	'InitTuan', # 拼团
	'/wx/tuan',		'Tuan',
	'/wx/init_tuan_list',	'InitTuanList', # 我的拼团
	'/wx/tuan_list',	'TuanList',
	'/wx/init_tuan_share',	'InitTuanShare', # 拼团分享
	'/wx/tuan_share',	'TuanShare',
	'/wx/init_tuan_detail',	'InitTuanDetail', # 拼团详情页
	'/wx/tuan_detail',	'TuanDetail',

	'/wx/get_host',		'WxGetHost',
	'/wx/user_phone',	'WxPhone',
	'/wx/user_check_rand',	'WxCheckRand',

	'/wx/signature',	'WxSignature',
]

## ---- 分布式部署---------------------------------
app_dir = ['weixin']
app_list = []
for i in app_dir:
	tmp_list = ['%s.%s' % (i,x[:-4])  for x in os.listdir(i) if x[:2]!='__' and x.endswith('.pyc')]
	app_list.extend(tmp_list)
#print app_list

for i in app_list:
	# __import__('pos.audit', None, None, ['*'])
	tmp_app = __import__(i, None, None, ['*'])
	urls.extend((tmp_app.url, i+'.handler'))

#-----------------------------------------------------
