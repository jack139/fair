#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib, urllib, httplib, time
from cgi import FieldStorage

def concat_params(params):
	pairs = []
	for key in sorted(params):
		#if key == 'sig':
		#continue
		val = params[key]
		if isinstance(val, unicode):
			val = urllib.quote_plus(val.encode('utf-8'))
		elif isinstance(val, str):
			val = urllib.quote_plus(val)
		if not isinstance(val, FieldStorage):
			pairs.append("{0}={1}".format(key, val))
	return '&'.join(pairs)


def gen_sig(path_url, params, consumer_secret):
	params = concat_params(params)

	to_hash = u'{0}?{1}{2}'.format(
		path_url, params, consumer_secret
	).encode('UTF-8').encode('hex')
	sig = hashlib.new('sha1', to_hash).hexdigest()
	return sig

def elm_port(restaurant_info_path_url,params,method):
	now_time = time.time().__long__()
	base_url = 'v2.openapi.ele.me'
	consumer_key = '3806191616'
	consumer_secret = '6dc6dba638b3da975464055a7d227854cb66776b'
	path_url = 'http://{0}{1}'.format(base_url, restaurant_info_path_url)
	system_params = {}
	system_params['consumer_key'] = consumer_key
	system_params['timestamp'] = now_time
	
	all_params = dict(params, **system_params)
	sig = gen_sig(path_url, all_params, consumer_secret)

	system_params['sig'] = sig
	conn = httplib.HTTPConnection(base_url, strict = False, timeout = 60)
	if method=='GET':
		path_url = '{0}?{1}'.format(path_url, concat_params(dict(system_params,**params)))
		conn.request(method, url = path_url)
	else:
		path_url = '{0}?{1}'.format(path_url, concat_params(system_params))
		headers = {'Content-Type' : 'application/x-www-form-urlencoded'}
		bf = concat_params(params)
		conn.request(method, url = path_url, body = bf, headers = headers)
	response = conn.getresponse().read()
	conn.close()
	return response
