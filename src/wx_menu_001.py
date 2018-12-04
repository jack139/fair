#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, urllib
import json
#from config import setting

# 东南
wx_appid='wxa84493ca70802ab5'
wx_secret='d4624c36b6795d1d99dcf0547af5443d'

wx_menu={
	'button':[
		{
			'type' : 'view',
			'name' : '拼团下单',
			'url'  : 'http://wxdn.urfresh.cn/wx/init_tuan',
		},
		{
			'name':'我的掌柜',
			'sub_button':[
				{
					'type' :'view',
					'name' :'我的拼团',
					'url'  : 'http://wxdn.urfresh.cn/wx/init_tuan_list',
				},
				{
					'type' :'view',
					'name' :'我的订单',
					'url'  : 'http://wxdn.urfresh.cn/wx/init_my_order',
				},
				{
					'type' :'view',
					'name' :'我的地址簿',
					'url'  : 'http://wxdn.urfresh.cn/wx/init_my_address',
				},
				#{
				#	'type' :'view',
				#	'name' :'我的抵用劵',
				#	'url'  : 'http://wx.urfresh.cn/wx/init_my_coupon',
				#},
				#{
				#	'type' :'view',
				#	'name' :'绑定手机',
				#	'url'  : 'http://wx.urfresh.cn/wx/init_my_bind',
				#},
				#{
				#	'type' : 'view',
				#	'name' : '下载App',
				#	'url'  : 'http://app.urfresh.cn/u',
				#}
			]
		},
		{
			'name':'在线客服',
			'sub_button':[
				{
					'type' :'view',
					'name' :'我要售后',
					'url'  : 'http://mp.weixin.qq.com/s?__biz=MzA5NjUzNjQ0Ng==&mid=400493586&idx=1&sn=a3682fea8c21c301a364ed5145b1eb51&scene=1&srcid=1117bAat0p4070AFeepjdCiE&key=d4b25ade3662d64318d9c7c092afa969e72c918e9f8a735e154430fe7e2b5842833bf7b6a97e00dab0c4ad9f03c1525f&ascene=0&uin=MjY2ODIxNjE4MQ%3D%3D&devicetype=iMac+MacBookPro5%2C4+OSX+OSX+10.11.1+build(15B42)&version=11020201&pass_ticket=LXvnLYfLNMKlPoVIsdMHEi8jXfVBU6Psga3EPrF2kVMGphDP1AtA%2Fjx51dYN7%2FFz',
				},
				{
					'type' :'view',
					'name' :'发货承诺',
					'url'  : 'http://mp.weixin.qq.com/s?__biz=MzA5NjUzNjQ0Ng==&mid=400491802&idx=1&sn=cf461d897222dbdbfcace2b7936a35dd&scene=1&srcid=1117OqiyP78dBkV9haSsOX7z&key=d4b25ade3662d643a596e0da074cd22cf11ea6040d520afeef0826ac1f55b899434f2c9e0cbb79729cbf66afc8ac8b1e&ascene=0&uin=MjY2ODIxNjE4MQ%3D%3D&devicetype=iMac+MacBookPro5%2C4+OSX+OSX+10.11.1+build(15B42)&version=11020201&pass_ticket=LXvnLYfLNMKlPoVIsdMHEi8jXfVBU6Psga3EPrF2kVMGphDP1AtA%2Fjx51dYN7%2FFz',
				},
				{
					'type' :'click',
					'name' :'我有建议',
					'key'  : 'CLICK_SUGGEST',
				},
				{
					'type':'click',
					'name':'在线客服',
					'key'  : 'CLICK_SERVICE',
				},
			]
		}
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

