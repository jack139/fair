#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, urllib
import json
#from config import setting

# U掌柜
wx_appid='wx2527355bfd909dbe'
wx_secret='49e8eb83c3fce102215a92047e8e9290'

wx_menu={
	'button':[
		{
			'type' : 'view',
			'name' : '立即下单',
			'url'  : 'http://wx.urfresh.cn/wx/init_fair',
		},
		{
			'name':'我的掌柜',
			'sub_button':[
				{
					'type' :'view',
					'name' :'我的订单',
					'url'  : 'http://wx.urfresh.cn/wx/init_my_order',
				},
				{
					'type' :'view',
					'name' :'我的地址簿',
					'url'  : 'http://wx.urfresh.cn/wx/init_my_address',
				},
				{
					'type' :'view',
					'name' :'我的抵用劵',
					'url'  : 'http://wx.urfresh.cn/wx/init_my_coupon',
				},
				{
					'type' :'view',
					'name' :'绑定手机',
					'url'  : 'http://wx.urfresh.cn/wx/init_my_bind',
				},
				{
					'type' : 'view',
					'name' : '下载App',
					'url'  : 'http://app.urfresh.cn/u',
				}
			]
		},
		#{
		#	'type':'view',
		#	'name':'双11免单',
		#	'url':'http://wx.urfresh.cn/static/hb/003.html',
		#},
		#{
		#	'type':'click',
		#	'name':'双11红包',
		#	'key'  : 'CLICK_WAIT',
		#},
		{
			'type':'view',
			'name':'邀请有礼',
			'url':'http://img.urfresh.cn/image/product/wxts/wxts_page.html?20151125c',
		},
		#{
		#	'type' : 'click',
		#	'name' : '精选团购',
		#	'key'  : 'CLICK_WAIT',
		#},


		#{
		#	'name':'关于我们',
		#	'sub_button':[
		#		{
		#			'type' : 'click',
		#			'name' : '最新消息',
		#			'key'  : 'PPT_NEWS',
		#		},
		#		{
		#			'type':'view',
		#			'name':'下载App',
		#			'url':'http://app.urfresh.cn/u',
		#		},
		#		{
		#			'type':'view',
		#			'name':'关于我们',
		#			'url':'http://www.urfresh.cn',
		#		}
		#	]
		#}
	]
}

def get_token():
	url='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
		(wx_appid, wx_secret)
	f=urllib.urlopen(url)
	data = f.read()
	f.close()

	t=json.loads(data)
	if t.has_key('access_token'):
		return t['access_token']
	else:
		return ''

def creat_menu(access_token):
	t=json.dumps(wx_menu, ensure_ascii=False)
	f = urllib2.urlopen(
		url	= 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s' % access_token,
		data	= t
		)
	ret=f.read()
	print ret

if __name__ == '__main__':
	my_token=get_token()
	#my_token='cI4OABcORaGjqdXhQmfGLbPv0CHgSxQpQmUsAJeNyLhe8Fy5i_L6NcB6bTze59QXvbXoMcKQXsV9Lo6TLCScYA'
	print my_token

	creat_menu(my_token)

