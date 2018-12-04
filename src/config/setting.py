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

web_serv_list={'web1' : ('192.168.2.99','192.168.2.99')}  # 

local_ip=web_serv_list['web1'][1]

cli = {'web'  : MongoClient(web_serv_list['web1'][0]),}
# MongoClient('10.168.11.151', replicaset='rs0')  # replica set
# MongoClient('10.168.11.151', replicaset='rs0', readPreference='secondaryPreferred') # 使用secondary 读
      
db_web = cli['web']['fair_db']
db_web.authenticate('ipcam','ipcam')

thread_num = 1
auth_user = ['test']
cs_admin = ['cs0']

tmp_path = '/usr/local/nginx/html/fair/static/tmp'
logs_path = '/usr/local/nginx/logs'
image_store_path = '/usr/local/nginx/html/fair/static/image/product'

default_shop='55837fd9ec6ef238912fab89'
B3_shop='55837fd9ec6ef238912fab89'
PT_shop={
	'001' : '564708a2ec6ef2206f57043c', # 东南
	'002' : '', # 华北
	'003' : '', # 华东
}
app_host='app.urfresh.cn'
wx_host='wx.urfresh.cn'
image_host='image.urfresh.cn'
notify_host='app.urfresh.cn'
app_pool=['app.urfresh.cn']

WX_store = {
	'000' : { # 测试
		'wx_appid' : 'wxb920ef74b6a20e69',
		'wx_appsecret' : 'ddace9d14b3413c65991278f09a03896',
		'mch_id' : '1242104702',
	},
	'001' : { # 东南
		'wx_appid' : 'wxa84493ca70802ab5',
		'wx_appsecret' : 'd4624c36b6795d1d99dcf0547af5443d',
		'mch_id' : '1284728201',
	},
	'002' : { # 华北
		'wx_appid' : 'wx64a0c20da3b0acb7',
		'wx_appsecret' : 'd4624c36b6795d1d99dcf0547af5443d',
		'mch_id' : '1284420901',
	},
	'003' : { # 华东
		'wx_appid' : 'wx2527355bfd909dbe',
		'wx_appsecret' : '49e8eb83c3fce102215a92047e8e9290',
		'mch_id' : '1253845801',
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

http_port=80
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
