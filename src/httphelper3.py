#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
import time
import socket, urllib, urllib3
import json, base64, random, hashlib
from config import setting


# 返回结果
E_OK		= 0
E_QUERY		= -1
E_JSON		= -2
E_DATA		= -3
E_STATUS	= -4

#
# ----------------- define about connection ---------------------------------------------
#

CONN_TIMEOUT = 180
socket.setdefaulttimeout(CONN_TIMEOUT)

urllib3.disable_warnings()

# cookie pool
cookie_pool = {}

# connection pool
conn_pool = {}

user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

# webpy专用，不使用代理
conn_pool['webpy'] = urllib3.PoolManager(num_pools=10, timeout=CONN_TIMEOUT, retries=False)
cookie_pool['webpy'] = {}

#
# ----------------- HTTP GET/POST & Cookie ---------------------------------------------
#

def random_proxy():
	return 'http://%s:8888' % setting.proxy_list[random.randint(0,len(setting.proxy_list)-1)]

def new_cookie(pool_id, name, value): # 添加新cookie
	global cookie_pool
	if cookie_pool.has_key(pool_id):
		cookie_pool[pool_id][name] = value
	else:
		cookie_pool[pool_id] = { name : value }

def get_cookie(pool_id): 
	if cookie_pool.has_key(pool_id):
		return cookie_pool[pool_id]
	else:
		return {}

def set_cookie(pool_id, c):
	global cookie_pool
	if c==None:
		cookie_pool[pool_id]={}
	else:
		cookie_pool[pool_id]=c

def clear_cookie(pool_id):
	set_cookie(pool_id, None)

def remove_session_cookie(pool_id):
	global cookie_pool
	if cookie_pool.has_key(pool_id):
		cookie_pool[pool_id].pop('BIGipServerotn', None)
		cookie_pool[pool_id].pop('JSESSIONID', None)

def new_pool(pool_id):
	global conn_pool
	#if setting.enable_proxy:
		#pool = urllib3.ProxyManager(setting.http_proxy, num_pools=50, timeout=CONN_TIMEOUT, retries=False)
	#else:
	#	pool = urllib3.PoolManager(num_pools=50, timeout=CONN_TIMEOUT, retries=False)
	pool = urllib3.ProxyManager(random_proxy(), num_pools=50, timeout=CONN_TIMEOUT, retries=False)
	conn_pool[pool_id]=pool
	return pool

def get_pool(pool_id):
	if conn_pool.has_key(pool_id):
		return conn_pool[pool_id]
	else:
		print 'get_pool(): %s not found!' % pool_id 
		return None

def set_todo(pool_id, new_cookie=None):
	# 添加链接，如果不存在
	if not conn_pool.has_key(pool_id):
		new_pool(pool_id)
	# 设置 cookie
	set_cookie(pool_id, new_cookie)
	print 'set_todo(): %s - %s' % (pool_id, conn_pool[pool_id].proxy.host)
	return get_pool(pool_id)

def close_pool(pool_id):
	global conn_pool
	# 清除连接
	if conn_pool.has_key(pool_id):
		conn_pool.pop(pool_id, None)
	# 清除cookie
	clear_cookie(pool_id)

def http_header(pool_id, host=None, origin=None, refer=None, more=None, isPOST=True):
	header={}
	header['Connection'] = 'keep-alive'
	header['Accept'] = '*/*'
	header['Accept-Language'] = 'zh-CN,zh;q=0.8'
	header['Accept-Encoding'] = 'gzip,deflate'
	header['User-Agent'] = user_agent
	if isPOST:
		header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
	if more!=None:
		for h in more:
			header[h[0]] = h[1]
	if host!=None:
		header['Host'] = host
	if origin!=None:
		header['Origin'] = origin
	if refer!=None:
		header['Referer'] = refer
	if len(cookie_pool[pool_id])>0:
		header['Cookie'] = '; '.join('%s=%s' % (k,v) for (k,v) in cookie_pool[pool_id].items())
	return header

def http_do_request(pool_id, method, url, header, body=None):
	#print body
	try:
		pool = get_pool(pool_id)
		#print pool, method, url, header
		r = pool.urlopen(method, url, headers=header, body=body)

		# 处理 set-cookie
		if 'set-cookie' in r.headers.keys():
			global cookie_pool
			l = r.headers['set-cookie'].split(',')
			for i in l:
				t = i.split(';')[0].split('=')
				if len(t)==2: 
					# cookie变量里有逗号！！！ 要避免！
					cookie_pool[pool_id][t[0].strip()] = t[1].strip()

		if r.status<500: #r.status==200 or r.status==405:
			return r.data
		else:
			print 'HTTP ERROR: ', r.status, url
			return None

	except Exception,e: 
		print '%s: %s (%s)' % (type(e), e, url)
		return None

def http_get(pool_id, url, host=None, origin=None, refer=None, more=None): # 
	# GET
	print url
	header = http_header(pool_id, host, origin, refer, more, isPOST=False)
	return http_do_request(pool_id, 'GET', url, header)

def http_post(pool_id, url, para, host=None, origin=None, refer=None, more=None, json=True): # para 是字典格式的参数(json=False)
	# POST
	if json:
		data = para
	else:
		data = '&'.join(['%s=%s' % (str(k),str(v)) if v!=None else str(k) for (k,v) in para.items()])
	print url
	print para
	header = http_header(pool_id, host, origin, refer, more)
	header['X-Requested-With'] = 'XMLHttpRequest'
	return http_do_request(pool_id, 'POST', url, header, data)

def http_do_post_encode_body(pool_id, url, body=None): # 用于打码
	#print body
	try:
		pool = get_pool(pool_id)
		#print url
		#print body
		r = pool.request_encode_body('POST', url, fields=body)

		if r.status<500: #r.status==200 or r.status==405:
			return r.data
		else:
			print 'HTTP ERROR: ', r.status, url
			return None

	except Exception,e: 
		print '%s: %s (%s)' % (type(e), e, url)
		return None

