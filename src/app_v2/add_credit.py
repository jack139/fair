#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
import urllib3
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

url = ('/app/(v3)/add_credit')

# 余额充值
class handler:        
	def POST(self, version='v3'):
		web.header('Content-Type', 'application/json')
		if version not in ('v2','v3'):
			return json.dumps({'ret' : -999, 'msg' : '版本错误！'})
		print 'version=',version

		param = web.input(app_id='', session='', cardcode='', sign='')

		if '' in (param.app_id, param.session, param.cardcode, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		uname = app_helper.app_logged(param.session) # 检查session登录
		if uname:
			#验证签名
			md5_str = app_helper.generate_sign([param.app_id, param.session, param.cardcode])
			if md5_str!=param.sign:
				return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

			#db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

			# 验证cardcode, 正确则充值
			r=db.credit_card.find_one({'card_no' : param.cardcode})
			if r:
				if r['used']!=0:
					return json.dumps({'ret' : -100, 'msg' : '该充值卡已被使用'})
				else:
					# 更新充值卡状态, 防止两个手机同时操作
					r2 = db.credit_card.find_one_and_update(
						{'card_no' : param.cardcode, 'used' : 0},
						{'$set':{
							'used'       : 1,
							'used_date'  : app_helper.time_str(),
							'used_uname' : uname['uname']
						}}, 
						{'used':1, 'card_sum':1}
					)

					if r2==None:
						return json.dumps({'ret' : -100, 'msg' : '该充值卡已被使用'})

					# 充值金额
					cash_to_add = r2['card_sum']

					# 充值操作
					db.app_user.update_one({'uname':uname['uname']},{
						'$inc'  : {'credit' : cash_to_add},
						'$push' : { 'credit_history' : (  # 专门记录余额消费
							app_helper.time_str(), 
							'余额充值',
							'＋%.2f' % cash_to_add,
							'卡号后4位: ****%s' % param.cardcode.encode('utf-8')[-4:]
						)}
					})
					db_credit=db.app_user.find_one({'uname':uname['uname']},{'credit':1})
					
					return json.dumps({'ret' : 0, 'data' : {
						'credit' : '%.2f' % db_credit['credit'],
						'message' : '充值成功！',
					}})
			else:					
				return json.dumps({'ret' : -100, 'msg' : '抱歉！正确输入格式为：卡号＋密码（加号不需输入），请重新输入'})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})
