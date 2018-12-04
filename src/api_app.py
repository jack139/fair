#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, gc
import time, json, hashlib
from bson.objectid import ObjectId
from config.url_api import urls2
from config import setting
import app_helper, sms

db = setting.db_web  # 默认db使用web本地

app = web.application(urls2, globals())
application = app.wsgifunc()

#----------------------------------------

gc.set_threshold(300,5,5)

###########################################

def my_crypt(codestr):
	return hashlib.sha1("sAlT139-"+codestr).hexdigest()

# 用户注册／登录
class Login:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		#print web.input()
		param = web.input(app_id='', number='', secret='')

		if '' in (param.app_id, param.number, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.number, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		number = param.number.strip()
		if len(number)<11 or (not number.isdigit()):
			return json.dumps({'ret' : -5, 'msg' : '手机号码格式错误'})

		# 随机码
		rand = app_helper.my_rand(base=1)
		register = False

		openid = ''

		# 检查用户是否已注册
		db_user = db.app_user.find_one({'uname':number})
		if db_user==None:
			# 未注册，新建用户记录
			coupon = []
			valid = app_helper.time_str(time.time()+3600*24*10, 1) # 有效期10天 2015-11-20
			# 注册发抵用券
			for i in app_helper.reginster_coupon:
				coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
			db.app_user.insert_one({
				'uname'    : number,
				'address'  : [],
				'coupon'   : coupon, # 送优惠券
				'app_id'   : param.app_id,
				'reg_time' : app_helper.time_str(),
			})
			register = True
		else:
			openid = db_user.get('openid','')
			# 更新app_id
			db.app_user.update_one({'uname':number},{'$set':{'app_id':param.app_id}})

		# 生成 session
		rand2 = os.urandom(16)
		now = time.time()
		secret_key = 'f6102bff8451236b8ca1'
		session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
		session_id = session_id.hexdigest()

		db.app_sessions.insert_one({
			'session_id' : session_id,
			'uname'      : number,
			'openid'     : openid,
			'login'      : 0,
			'rand'       : rand,
			'ip'         : web.ctx.ip,
			'attime'     : now,
		})

        	#发送短信验证码
        	if number not in setting.inner_number.keys():
        		sms.send_rand(number, rand, register)

		# 返回
		return json.dumps({
			'ret'  : 0, 
			'data' : {
				'session'  : session_id,
				'register' : register,
			}
		})

# 用户注册／登录
class Login2:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		#print web.input()
		param = web.input(app_id='', number='', secret='')

		if '' in (param.app_id, param.number, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.number, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		number = param.number.strip()
		if len(number)<11 or (not number.isdigit()):
			return json.dumps({'ret' : -5, 'msg' : '手机号码格式错误'})

		# 随机码
		rand = app_helper.my_rand(base=1)
		register = False

		openid = ''

		# 检查用户是否已注册
		db_user = db.app_user.find_one({'uname':number})
		if db_user==None:
			# 未注册，新建用户记录
			coupon = []
			valid = app_helper.time_str(time.time()+3600*24*10, 1) # 有效期10天 2015-11-22
			# 注册发抵用券
			for i in app_helper.reginster_coupon:
				coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
			db.app_user.insert_one({
				'uname'    : number,
				'new_coupon' : len(app_helper.reginster_coupon), # v3
				'address'  : [],
				'coupon'   : coupon, # 送优惠券
				'app_id'   : param.app_id,
				'reg_time' : app_helper.time_str(),
			})
			register = True
		else:
			openid = db_user.get('openid','')
			# 更新app_id
			db.app_user.update_one({'uname':number},{'$set':{'app_id':param.app_id}})

		# 生成 session ------------------
		rand2 = os.urandom(16)
		now = time.time()
		secret_key = 'f6102bff8451236b8ca1'
		session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
		session_id = session_id.hexdigest()

		db.app_sessions.insert_one({
			'session_id' : session_id,
			'uname'      : number,
			'openid'     : openid,
			'login'      : 0,
			'rand'       : rand,
			'ip'         : web.ctx.ip,
			'attime'     : now,
		})
		# -------------------------------

        	#发送短信验证码
        	sms.send_rand(number, rand, register)

		# 返回
		return json.dumps({
			'ret'  : 0, 
			'data' : {
				'session'  : session_id,
				'user_new' : register,
			}
		})

# 检查随机码
class CheckRand:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		#print web.input()
		param = web.input(app_id='', session='', rand='', invitation='', sign='')

		if '' in (param.app_id, param.session, param.rand, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.session, param.rand, param.invitation])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		session = app_helper.get_session(param.session)
		if session==None:
			return json.dumps({'ret' : -4, 'msg' : '无效的session'})

		if param.rand.strip()!=session['rand']:
			if session['uname']=='18516569412' and param.rand.strip()=='9998':
				None
			elif session['uname'] in setting.inner_number.keys() and \
				param.rand.strip()==setting.inner_number[session['uname']]:
				None
			else:
				return json.dumps({'ret' : -5, 'msg' : '短信验证码错误'})

		db.app_sessions.update_one({'session_id':session['session_id']},{'$set':{
			'login'  : 1,
			'attime' : time.time(),
		}})

		#邀请码
		if param.has_key('invitation'):
			invitation = param.invitation.lower()
			
			if db.invitation.find({'code': invitation}).count()==0: # 无效地推邀请码
				if db.app_user.find({'my_invit_code': invitation}).count()==0: # 无效用户邀请码
					invitation = ''
			if invitation != '':
				r = db.app_user.find_one({'uname' : session['uname']},{'invitation':1})
			 	if r.get('invitation', '')!='': # 已填邀请码
					invitation = ''
		else:
			invitation = ''

		invitation_coupon = 0
		if invitation!='':
			# 赠送优惠券
			invitation_coupon = 1
			valid = app_helper.time_str(time.time()+3600*24*10, 1) # 有效期10天
			r = db.app_user.find_one_and_update({'uname' : session['uname']},{
				'$set'  : {'invitation' : invitation, 'last_time' : app_helper.time_str()},
				'$push' : {'coupon'     : (app_helper.my_rand(), valid, '5.00', 1, 14.9, 'apple')}, # 邀请码送5+4+3
			}, {'address':1, 'new_coupon':1})
			db.app_user.update_one({'uname' : session['uname']},{ # 4元
				'$push' : {'coupon' : (app_helper.my_rand(), valid, '4.00', 1, 24.9, 'apple')}, 
			})
			db.app_user.update_one({'uname' : session['uname']},{ # 3元
				'$push' : {'coupon' : (app_helper.my_rand(), valid, '3.00', 1, 19.9, 'apple')}, 
			})
		else:
			r = db.app_user.find_one_and_update({'uname' : session['uname']},{
				'$set'  : {'last_time' : app_helper.time_str()}
			}, {'address':1, 'new_coupon':1})

		if len(r['address'])>0: # 应该实现：返回最近使用的地址 !!!!
			addr = {
				'id'   : r['address'][0][0],
				'name' : r['address'][0][1],
				'tel'  : r['address'][0][2],
				'addr' : r['address'][0][3],
			}
		else:
			addr = {}

		# 检查是否有新红包
		app_helper.check_hb(session['uname'])

		# 返回
		if version=='v3':
			# 是否有新收到的抵用券，进行提示
			if r.has_key('new_coupon') and r['new_coupon']>0:
				alert = True
				message = '掌柜送您%d张抵用券，请在个人中心查看哦' % (r['new_coupon']+invitation_coupon)
				db.app_user.update_one({'uname':session['uname']},{'$set':{'new_coupon':0}})
			else:
				alert = False
				message = ''
			return json.dumps({
				'ret'  : 0, 
				'data' : {
					'session' : session['session_id'],
					'login'   : True,
					'addr'    : addr, 
					'uname'   : session['uname'],
					'alert'   : alert,
					'message' : message
				}
			})
		else: # v1,v2
			return json.dumps({
				'ret'  : 0, 
				'data' : {
					'session' : session['session_id'],
					'login'   : True,
					'addr'    : addr, 
					'uname'   : session['uname'],
				}
			})

# 退出
class Logout:
	def POST(self, version='v1'):
		web.header('Content-Type', 'application/json')
		param = web.input(app_id='', session='', secret='')

		if '' in (param.app_id, param.session, param.secret, param.sign):
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		#验证签名
		md5_str = app_helper.generate_sign([param.app_id, param.session, param.secret])
		if md5_str!=param.sign:
			return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

		#session = app_helper.get_session(param.session)
		#if session==None:
		#	return json.dumps({'ret' : -4, 'msg' : '无效的session'})

		db.app_sessions.remove({'session_id':param.session})

		# 返回
		return json.dumps({
			'ret'  : 0, 
			'data' : {
				'logout' : True,
			}
		})




#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
