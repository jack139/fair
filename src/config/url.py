#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

urls = [
	'/',                'Login',
	'/login',           'Login',
	'/logout',          'Reset',
	'/settings_user',   'SettingsUser',
	'/article',         'Aticle',

	'/view_event',      'ViewEvent',
	'/crm',             'Crm',

	# 管理功能
	'/admin/user',         'AdminUser',
	'/admin/user_setting', 'AdminUserSetting',
	'/admin/user_add',     'AdminUserAdd',
	'/admin/self_setting', 'AdminSelfSetting',
	'/admin/sys_setting',  'AdminSysSetting',
	'/admin/status',       'AdminStatus',
	'/admin/data',         'AdminData',
]

## ---- 分布式部署---------------------------------
app_dir = ['plat', 'pos', 'stock', 'online', 'delivery', 'report']
app_list = []
for i in app_dir:
	tmp_list = ['%s.%s' % (i,x[:-4])  for x in os.listdir(i) if x[:2]!='__' and x.endswith('.pyc')]
	app_list.extend(tmp_list)
#print app_list

for i in app_list:
	# __import__('pos.audit', None, None, ['*'])
	tmp_app = __import__(i, None, None, ['*'])
	if not hasattr(tmp_app, 'url'):
		print tmp_app
		continue
	urls.extend((tmp_app.url, i+'.handler'))

#-----------------------------------------------------
