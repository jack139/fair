#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

urls = [
	'/app/first_hand',	'FisrtHand',
	'/app/get_host',	'GetHost',
	'/app/alipay_notify',	'AlipayNotify',
	'/app/wxpay_notify',	'WxpayNotify',

	'/app/(v2|v3)/first_hand',	'FisrtHand_v2',
	'/app/(v2|v3)/get_host',	'GetHost',
	'/app/(v2|v3)/alipay_notify',	'AlipayNotify',
	'/app/(v2|v3)/wxpay_notify',	'WxpayNotify',
]

urls2 = [
	'/app/user_login',	'Login',
	'/app/user_login2',	'Login2',
	'/app/user_check_rand',	'CheckRand',
	'/app/user_logout',	'Logout',

	'/app/(v2|v3)/user_login',	'Login2',
	'/app/(v2|v3)/user_check_rand',	'CheckRand',
	'/app/(v2|v3)/user_logout',	'Logout',
]

## ---- 分布式部署---------------------------------
app_dir = ['app', 'app_v2']
app_list = []
for i in app_dir:
	tmp_list = ['%s.%s' % (i,x[:-4])  for x in os.listdir(i) if x[:2]!='__' and x.endswith('.pyc')]
	app_list.extend(tmp_list)
#print app_list

for i in app_list:
	# __import__('pos.audit', None, None, ['*'])
	tmp_app = __import__(i, None, None, ['*'])
	urls2.extend((tmp_app.url, i+'.handler'))

#-----------------------------------------------------
