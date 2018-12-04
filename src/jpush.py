#!/usr/local/bin/python
#-*- coding:utf-8 -*-

import socket, urllib3, json, base64

# 极光推送

appKey = '142eadec0a13709d9ab3f299'
masterSecret = '3de37b1522eb6987f4b82842'
authorization = 'Basic %s' % base64.b64encode('%s:%s' % (appKey,masterSecret))

CONN_TIMEOUT = 180
socket.setdefaulttimeout(CONN_TIMEOUT)
urllib3.disable_warnings()

def jpush(text, phone=None, prod=True):
	# POST
	print 'jpush()'

	if phone==None:
		audience = 'all'
	else:
		#audience = {'alias':[phone]}
		audience = {'alias':[i.strip() for i in phone.split(',')]}

	notification = {
		'android' : { 'alert' : text },
		'ios'     : { 'alert' : text },
	}

	message = {
		'msg_content'  : text,
		'content_type' : 'text',
	}

	conn = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)

	body0 = {
		'platform'     : 'all',
		'audience'     : audience,
		'notification' : notification,
		#'message'      : message,
		'options'      : {'apns_production':prod}
	}
	header = {
		'Authorization' : authorization,
		'Content-Type'  : 'application/json',
	}
	body = json.dumps(body0)

	print body0
	r = conn.urlopen('POST', 'https://api.jpush.cn/v3/push', headers=header, body=body)

	if r.status<500: #r.status==200 or r.status==405:
		print r.data
		return r.data
	else:
		print r.status
		return False

def jpush_ios(text, phone=None, prod=True):
	# POST
	print 'jpush()'

	if phone==None:
		audience = 'all'
	else:
		#audience = {'alias':[phone]}
		audience = {'alias':[i.strip() for i in phone.split(',')]}

	notification = {
		#'android' : { 'alert' : text },
		'ios'     : { 'alert' : text },
	}

	message = {
		'msg_content'  : text,
		'content_type' : 'text',
	}

	conn = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)

	body0 = {
		'platform'     : ['ios'],
		'audience'     : audience,
		'notification' : notification,
		'message'      : message,
		'options'      : {'apns_production':prod}
	}
	header = {
		'Authorization' : authorization,
		'Content-Type'  : 'application/json',
	}
	body = json.dumps(body0)

	print body0
	r = conn.urlopen('POST', 'https://api.jpush.cn/v3/push', headers=header, body=body)

	if r.status<500: #r.status==200 or r.status==405:
		print r.data
		return r.data
	else:
		print r.status
		return False

