#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import web
import time, datetime, os, hashlib
import urllib, urllib3, json
import re
from config import setting
#from app_settings import *  # app_settings.py将拼接在末尾

db = setting.db_web

ISOTIMEFORMAT=['%Y-%m-%d %X', '%Y-%m-%d', '%Y%m%d%H%M']

def time_str(t=None, format=0):
    return time.strftime(ISOTIMEFORMAT[format], time.localtime(t))

def validateEmail(email):
    if len(email) > 7:
      if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
	return 1
    return 0

RAND_BASE=[
	'abcdefghijklmnopqrstuvwxyz',
	'0123456789',
]

def my_rand(n=4, base=0):
	import random
	return ''.join([random.choice(RAND_BASE[base]) for ch in range(n)])


# 红包设置
HB = { # hb_id : [begin_date, end_date, max_money]
	'001' : ['2015-09-16', '2015-09-20', 200000],
	'002' : ['2015-10-17', '2015-10-18', 200000],
}



#  -------------------------------------------

WHITE_LIST = [
	'18516298955',
	'18616569698',
	'15021873573',
	'13806077726',
	'18721816520',
	'13671575571',
	'13917646258',
	'13636699694',
	'13917458078',
	'18616833493',
	'18017880388',
	'18501733810',
	'13916460238',
	'18516569412',
	'99990000100', # 虚拟号
	'99990000101',
	'99990000102',
	'99990000103',
	'99990000104',
	'99990000105',
	'99990000106',
	'99990000107',
	'99990000108',
	'99990000109',
	'99990000110',
	'18521509216', # 1号店
	'13764938315', # 隔壁 祖冲之路887弄84号505
	'15001795227', # 沈阳老婆
	'15556936375', # 地推经理
	'13817011961', # 1号店
	'13918119003', # 1号店
	'13194084665', # 
	'13916661041', # 1号店
	'18651458287', # 张江店长
	'18521757501', # 1号店
	'17721259512', # 加盟商
	'15601617030', # u 掌柜
	'13524684772', # bruce
	'18662570523', # bruce
	'15921787883', # bruce
]

# 查询session
def get_session(session_id):
	return db.app_sessions.find_one_and_update({'session_id':session_id},{'$set':{'attime':time.time()}})

# 检查session登录状态
def logged(session_id):
	session = get_session(session_id)
	if session==None:
		return None
	else:
		#db.app_user.update_one({'uname' : session['uname']},{
		#	'$set'  : {'last_time' : time_str()}
		#})
		if session['login']==1: # 登录后返回uname
			return session['uname']
		else:
			return None

# 检查session登录状态, 合并app与微信订单
def app_logged(session_id):
	session = get_session(session_id)
	if session==None:
		return None
	else:
		#db.app_user.update_one({'uname' : session['uname']},{
		#	'$set'  : {'last_time' : time_str()}
		#})
		if session['login']==1: # 登录后返回uname,openid
			return {'uname' : session['uname'], 'openid': session.get('openid','')}
		else:
			return None

# 检查openid
def check_openid(openid):
	r = db.app_user.find_one_and_update(
		{'openid' : openid},
		{'$set'   : {'last_time' : time_str()}},
		{'uname' : 1, 'openid':1}
	)
	if r: 
		return {'uname' : r.get('uname',''), 'openid': r['openid']}
	else:
		return None

# 微信检查session登录状态
def wx_logged(session_id):
	session = get_session(session_id)
	if session==None:
		return None
	else:
		#db.app_user.update_one({'uname' : session['uname']},{
		#	'$set'  : {'last_time' : time_str()}
		#})
		if session['login']==1: # 登录后返回uname
			#return session['uname']
			return {'uname' : session['uname'], 'openid': session['openid']}
		else:
			return None

def generate_sign(c): # c时列表，c[0]一定是app_id
	db_dev = db.app_device.find_one({'app_id' : c[0]}, {'private_key':1})
	if db_dev==None:
		return None
		#return json.dumps({'ret' : -3, 'msg' : 'app_id错误'})
	else:
		#验证签名
		sign_str = '%s%s' % (db_dev['private_key'], ''.join(i for i in c))
		return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()



#-- 检查账号是否有红包
def check_hb(phone):
	db_hb = db.hb_store.find({'phone':phone, 'added':{'$exists':False}})
	for i in db_hb:
		if i['hb_id']=='003':
			if i['hb_money']==20: # new
				new_c = (my_rand(),'2015-11-30','5.00', 1, 14.9, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
				new_c = (my_rand(),'2015-11-30','15.00', 1, 59, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
			elif i['hb_money']==30: # old
				new_c = (my_rand(),'2015-11-30','6.00', 1, 29, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
				new_c = (my_rand(),'2015-11-30','9.00', 1, 39, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
				new_c = (my_rand(),'2015-11-30','15.00', 1, 59, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
			else: # wb
				new_c = (my_rand(),time_str(format=1),'19.80', 1, 19.9, 'apple')
				db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
			db.hb_store.update_one({'_id':i['_id']},{'$set':{'added':1}})
		else:
			# 添加到用户信息
			new_c = (my_rand(),i['expired_date'].encode('utf-8'),'%.2f' % float(i['hb_money']), 1)
			print 'add coupon', str(new_c)
			db.app_user.update_one({'uname':phone},{'$push': {'coupon':new_c}})
			db.hb_store.update_one({'_id':i['_id']},{'$set':{'added':1}})


# 第三方对照表使用的db
db_rep = setting.cli['web']['report_db']
db_rep.authenticate('owner','owner')

# elm 修改库存
def elm_modify_num(shop_id, product_id):
	# 忽略称重商品和物料
	if product_id[0] != 'w' and product_id[1] != '0' and product_id[2] != '2':
		r3 = db.sku_store.find_one({'product_id' : product_id}, {'list_in_app':1, 'app_title':1})
		if r3==None:
			print 'elm_modify_num: 未找到商品'
		elif r3['list_in_app']==3: # B3商品
			print 'elm_modify_num: 忽略B3商品'
		else:
			if r3['list_in_app']==0: # app下架的商品，elm也下架
				r = {'num':0}
			else:
				# 取当前库存
				r = db.inventory.find_one({
					'product_id' : product_id,
					'shop'       : shop_id,
				}, {'num':1})
			if r:
				# 准备更新elm数据
				db_rep.inv_modify.insert_one({
					'shop_id'    : shop_id,
					'product_id' : product_id,
					'num'        : r['num'],
					'title'      : r3['app_title'],
				})
			else:
				print 'elm_modify_num: 未找到商品'
	else:
		print 'elm_modify_num: 忽略称重商品和物料'

# 生成order_id
def get_new_order_id(version='v1'):
	cc=1
	while cc!=None:
		# order_id 城市(1位)+日期时间(6+4位)+随机数(5位)+版本
		order_id = 'n1%s%s%s' % (time_str(format=2)[2:],my_rand(5),version[-1])
		cc = db.order_app.find_one({'order_id' : order_id},{'_id':1})
	return order_id

# 取得设备类型
def get_devive_type(app_id):
	db_dev = db.app_device.find_one({'app_id':app_id},{'type':1})
	if db_dev:
		return db_dev['type']
	else:
		return ''

# 微信客服接口回信息

wx_appid=setting.wx_setting['wx_appid']
wx_secret=setting.wx_setting['wx_appsecret']

# 获取access_token，与wx.py 中相同
def get_token(force=False): # force==True 强制刷新
	print 'region: ', setting.region_id
	if not force:
		db_ticket = db.jsapi_ticket.find_one({'region_id':setting.region_id})
		if db_ticket and int(time.time())-db_ticket.get('token_tick', 0)<3600:
			if db_ticket.get('access_token', '')!='':
				print db_ticket['access_token']
				return db_ticket['access_token']

	url='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
		(wx_appid, wx_secret)
	f=urllib.urlopen(url)
	data = f.read()
	f.close()

	t=json.loads(data)
	if t.has_key('access_token'):
		print t 
		db.jsapi_ticket.update_one({'region_id':setting.region_id},
			{'$set':{'token_tick':int(time.time()), 'access_token':t['access_token']}},upsert=True)
		return t['access_token']
	else:
		db.jsapi_ticket.update_one({'region_id':setting.region_id},
			{'$set':{'token_tick':int(time.time()), 'access_token':''}},upsert=True)
		return ''

def wx_reply_msg0(openid, text, force=False):
	text0 = text.encode('utf-8') if type(text)==type(u'') else text
	body_data = '{"touser":"%s","msgtype":"text","text":{"content":"%s"}}' % (str(openid), text0)
	urllib3.disable_warnings()
	http = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
	url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s'%get_token(force)
	try:
		r = http.request('POST', url, 
			headers={'Content-Type': 'application/json'},
			body=body_data)
		if r.status==200:
			return json.loads(r.data)
		else:
			print 'http fail: ', r.status
			return None
	except Exception,e: 
		print '%s: %s (%s)' % (type(e), e, url)
		return None


def wx_reply_msg(openid, text):
	r = wx_reply_msg0(openid, text)
	if r==None or r.get('errcode', 0)!=0:
		# 发送失败，强制刷新token后再发一次
		print r
		#r = wx_reply_msg0(openid, text, True)
	#print r
	return r

