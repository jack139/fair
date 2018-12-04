#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 趣送推送给urfresh

import urllib3, web, json #, requests
from config import setting
import hashlib

db = setting.db_web
#urls = (
#	'/qusong_json', 'urfresh'
#	)
private_key = 'MaVGJpmvGAAFMEgJCDzfDYj8wqx3EYnp'

url = ('/online/qusong_json')

# 签名按method+path+timestamp+private_key拼接字符串
def sign(method, path, time_stamp, private_key):
	string_to_sign = method + path + time_stamp + private_key
	return hashlib.sha1(string_to_sign).hexdigest()
	
class handler:
	def POST(self):
		header_type = web.ctx.env.get('CONTENT_TYPE')
		if not web.ctx.env.has_key('HTTP_X_UF_TIMESTAMP') or not web.ctx.env.has_key('HTTP_X_UF_SIGN') or header_type != 'application/x-www-form-urlencoded':
			return json.dumps({'ret': 2006, 'msg': '缺少头信息'})

		time_stamp = web.ctx.env['HTTP_X_UF_TIMESTAMP']
		signature_qusong = web.ctx.env['HTTP_X_UF_SIGN']

		# 获取客户端请求的路径
		path = web.ctx.env['PATH_INFO']
		print path
		signature_urfresh = sign('POST', path, time_stamp, private_key)

		if signature_qusong != signature_urfresh:
			return json.dumps({'ret': 1006, 'msg': '签名错误'})
		
		data = web.input(fail_detail='')

		# print json.load(data)
		print data
		print data.keys()
		print len(data.keys())
		# print data['{}']

		# 判断输入参数
		if len(data.keys()) == 1:
			return json.dumps({'ret': 2003, 'msg': '空值错误'})

		if data.get('order_id') == None or data.get('order_status') == None or (data.get('order_status') == 'FAIL' and data.get('fail_detail') == ''):
			return json.dumps({'ret': 2001, 'msg': '缺少参数'})

		if len(data.keys()) != 3:
			return json.dumps({'ret': 2004, 'msg': '值长度错误'})


		# param_key = [('order_id', 'order_status', 'fail_detail'), ('order_id', 'order_status')]

		# if not tuple(data.keys()) in param_key:
		# 	return json.dumps({'ret': 2003, 'msg': '参数错误'})

		# for key in data.keys():
		# 	if not key in ['order_id', 'order_status', 'fail_detail']:
		# 		return json.dumps({'ret': 2003, 'msg': '参数错误'})

		db_order = db.order_app.find_one({'order_id': data['order_id']})
		# order_id = [item['order_id'] for item in db_order]
		print db_order

		if data['order_status'] == 'ONROAD' and  db_order['status'] != 'DISPATCH' or db_order is None:
			return json.dumps({'ret': 3001, 'msg': 'order_id不存在'})

		# 更改status状态
		if data["fail_detail"] == '':
			db.order_app.update_one({'order_id': data['order_id']}, {'$set' : {'status': data['order_status']}})
		else:			
			db.order_app.update_one({'order_id': data['order_id']}, {'$set': {'status': data['order_status'], 'fail_detail': data['fail_detail']}})			

		return json.dumps({'ret' : 204, 'msg' : 'OK'})

#if __name__ == "__main__":
#	app = web.application(urls, globals())
#	app.run()