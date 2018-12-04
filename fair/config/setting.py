#!/usr/bin/env python
# -*- coding: utf-8 -*-
import web
from pymongo import MongoClient

#####
debug_mode = True   # Flase - production, True - staging
#####
#
enable_proxy = True
http_proxy = 'http://192.168.2.108:8888'
https_proxy = 'https://192.168.2.108:8888'
proxy_list = ['192.168.2.103']
enable_local_test = True
#####

web_serv_list={'web1' : ('192.168.2.99','192.168.2.99')}

local_ip=web_serv_list['web1'][1]

cli = {
    'web'  : MongoClient(web_serv_list['web1'][0], connect=False),
    'web0'  : MongoClient(web_serv_list['web1'][0], connect=False),
}
# MongoClient('10.168.11.151', replicaset='rs0', readPreference='secondaryPreferred') # 使用secondary 读
# MongoClient('mongodb://10.168.11.151:27017,10.252.95.145:27017,10.252.171.8:27017/?replicaSet=rs0')
db_web = cli['web']['fair_db']
db_web.authenticate('ipcam','ipcam')

db_primary = cli['web0']['fair_db']
db_primary.authenticate('ipcam','ipcam')

db_rep = cli['web']['report_db']
db_rep.authenticate('owner','owner')

thread_num = 1
auth_user = ['test']
cs_admin = ['cs0']

tmp_path = '/usr/local/nginx/html/fair/static/tmp'
logs_path = '/usr/local/nginx/logs'
image_store_path = '/usr/local/nginx/html/fair/static/image/product'

default_shop='55837fd9ec6ef238912fab89'
default_shop_name = '张江店'
MALL_shop='55b7ae5a5e0bdc3041c3f068'
B3_shop='55837fd9ec6ef238912fab89'
PT_shop={
	'001' : '56485b9e5e0bdc08ca99427e', # 东南
	'002' : '56c68ee05e0bdc2a5b5b02d8', # 华北
	'003' : '5659e52e5e0bdc6714ccf576', # 华东
	'004' : '572ff0c45e0bdc49b5e39c4a', # 鲁豫
	'005' : '572ff0ec5e0bdc3bcb7e7f46', # 西南
	'006' : '572ff1185e0bdc7fae093c58', # 华南
	'007' : '572ff16e5e0bdc49b5e39c4c', # 华中
}
S48H_shop=[
	'55e26cb05e0bdc2219b049d1',  # 测试环境，嘉兴店, 2015-12-22, gt
]
app_host='app.urfresh.cn'
wx_host='wx.urfresh.cn'
image_host='image.urfresh.cn'
notify_host='app.urfresh.cn'
app_pool=['app.urfresh.cn']
https_image_host = 'https://%s/image/product' % image_host

WX_store = {
	'000' : { # 测试
		'wx_appid' : 'wxb920ef74b6a20e69',
		'wx_appsecret' : 'ddace9d14b3413c65991278f09a03896',
		'mch_id' : '1242104702',
	},
	'999' : { # 测试
		'wx_appid' : 'wxb920ef74b6a20e69',
		'wx_appsecret' : 'ddace9d14b3413c65991278f09a03896',
		'mch_id' : '1242104702',
	},
	'001' : { # 东南
		'wx_appid' : 'wxa84493ca70802ab5',
		'wx_appsecret' : '3476ff4cfb93282f57bcad06b7d6738c',
		'mch_id' : '1284728201',
	},
	'002' : { # 华北
		'wx_appid' : 'wx668ab1f5e949b6a3',
		'wx_appsecret' : 'fdb34c13b422a8ea1d79cbc24db2fe06',
		'mch_id' : '1312749701',
	},
	'003' : { # 华东
		'wx_appid' : 'wx2527355bfd909dbe',
		'wx_appsecret' : '49e8eb83c3fce102215a92047e8e9290',
		'mch_id' : '1253845801',
	},

	'004' : { # 鲁豫
		'wx_appid' : 'wx5069841a83340233',
		'wx_appsecret' : 'fc531d1cf5f2bd0051ac7813c65735f4',
		'mch_id' : '1341285301',
	},
	'005' : { # 西南
		'wx_appid' : 'wxfb8e590597fd0c53',
		'wx_appsecret' : '3f88ca6d1022521e1b222a480b18dcb2',
		'mch_id' : '1340914101',
	},
	'006' : { # 华南
		'wx_appid' : 'wx0ac545967efecaec',
		'wx_appsecret' : '19b2883051f47af63df1aeda748b5a4a',
		'mch_id' : '1340917901',
	},
	'007' : { # 华中
		'wx_appid' : 'wx1f903b630c65af7a',
		'wx_appsecret' : '2d87528c004616becdf5d44245cb7f46',
		'mch_id' : '1340896601',
	},

}

# region_id 来自文件
f=open('/region_id')
a=f.readlines()
f.close()
region_id = a[0].strip()

# 微信设置
wx_setting = WX_store[region_id]

order_fuffix=''
inner_number = {
	'99990000100' : '9998',
	'99990000101' : '3942',
	'99990000102' : '4345',
	'99990000103' : '2875',
	'99990000104' : '3492',
	'99990000105' : '0980',
	'99990000106' : '3482',
	'99990000107' : '5340',
	'99990000108' : '9873',
	'99990000109' : '2345',
	'99990000110' : '8653',
}

http_port=8000
https_port=443

mail_server='127.0.0.1'
sender='"Kam@Cloud"<kam@f8geek.com>'
worker=['2953116@qq.com']

web.config.debug = debug_mode

config = web.storage(
	email = 'jack139@gmail.com',
	site_name = 'ipcam',
	site_des = '',
	static = '/static'
)
