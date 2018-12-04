#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json, urllib, urllib3
import gc
from bson.objectid import ObjectId
from config.url_wx import urls
from config import setting
from config.mongosession import MongoStore
import app_helper, sms
from app_helper import time_str, get_token
try:
	import xml.etree.cElementTree as ET
except ImportError:
	import xml.etree.ElementTree as ET

db = setting.db_web  # 默认db使用web本地
#file_db = setting.db_file1

app = web.application(urls, globals())
application = app.wsgifunc()

#--session---------------------------------------------------
#web.config.session_parameters['cookie_name'] = 'uwx_session'
#web.config.session_parameters['secret_key'] = 'f6102bff8452386b8ca1'
#web.config.session_parameters['timeout'] = 86400
#web.config.session_parameters['ignore_expiry'] = True

#if setting.debug_mode==False:
#	### for production
#	session = web.session.Session(app, MongoStore(db, 'sessions'), 
#		initializer={'login': 0, 'privilege': 0, 'uname':'', 'openid':''})
#else:
#	### for staging,
#	if web.config.get('_session') is None:
#		session = web.session.Session(app, MongoStore(db, 'sessions'), 
#			initializer={'login': 0, 'privilege': 0, 'uname':'', 'openid':''})
#		web.config._session = session
#	else:
#		session = web.config._session

#----------------------------------------

gc.set_threshold(300,5,5)

# U掌柜 生产用
#wx_appid='wx2527355bfd909dbe'
#wx_secret='49e8eb83c3fce102215a92047e8e9290'

# F8KAM 测试用
#wx_appid='wxb920ef74b6a20e69'
#wx_secret='ddace9d14b3413c65991278f09a03896'

wx_appid=setting.wx_setting['wx_appid']
wx_secret=setting.wx_setting['wx_appsecret']


##############################################

def create_render(plain=False):    
	if plain: layout=None
	else: layout='layout'
	render = web.template.render('templates/wx', base=layout)
	return render

def check_wx_user(wx_user):
	db_wx=db.wx_user.find_one({'wx_user':wx_user},{'owner':1})
	if db_wx!=None: # 已登记
		return db_wx['owner']
	else: # 未登记
		db.wx_user.insert_one({'wx_user' : wx_user, 'owner': '', 'time' : time_str()})
		return ''

def bind_wx_user(wx_user, fair_user):
	check_wx_user(wx_user)
	db.wx_user.update_one({'wx_user':wx_user},{'$set': {'owner':fair_user}})

def reply_none():
	web.header("Content-Type", "text/plain") # Set the Header
	return ""

class PostMsg:
	def __init__(self, str_xml):
		self.xml=ET.fromstring(str_xml)
		self.fromUser=self.xml.find("FromUserName").text
		self.toUser=self.xml.find("ToUserName").text
		self.msgType=self.xml.find("MsgType").text
		self.key=''
	
	def reply_text(self, content):
		render = create_render(plain=True)
		return render.xml_reply(self.fromUser, self.toUser, int(time.time()), content)

	def reply_media(self, content):
		# 标题，说明，图片url，页面url
		#content = [(u'标题2', u'', u'', u'http://wx.f8geek.com/live2')]
		render = create_render(plain=True)
		return render.xml_media(self.fromUser, self.toUser, int(time.time()), content)		

	def text_process(self): # 处理文本消息回复
		content=self.xml.find("Content").text
		cmd0 = content.split()
		if u'免单' in cmd0[0].lower(): # 测试
			return self.reply_media([
				(u'魔都U粉会专享免单，人人有份！',u'',u'',
				u'http://mp.weixin.qq.com/s?__biz=MzI3OTAwODMyOQ==&mid=400211195&idx=1&sn=f3e41093c3b4594d8746fac4dd3f3106#rd')
			])
		if setting.region_id=='003': # 华东
			return self.reply_text( u"亲爱的客官你好，感谢您对我们的支持。上海外环内U掌柜鲜果零食均可享受19.9元包邮，1小时送达的服务。如有任何问题可拨打客服电话：400-966-9966，对果品不满意可立即退货或退款。")
		else:
			return self.reply_text( u"亲爱的客官你好，感谢您对我们的支持。如有任何问题可拨打客服电话：400-966-9966。")
	def event_process(self): # 处理事件请求
		event=self.xml.find("Event").text
		if event=='CLICK':
			self.key=self.xml.find("EventKey").text
			#print self.key
			if self.key=='CLICK_WAIT':
				return self.reply_text(u"敬请期待！")
			elif self.key=='CLICK_SERVICE':
				return self.reply_text(u"亲爱的客官，感谢您关注U掌柜拼团。在线客服服务每天9:00-20:00真人值守，全心全意为您服务！请客官概述一下您遇到的问题，我们将对应问题安排客服快速、有效的帮助您，谢谢")
			elif self.key=='CLICK_SUGGEST':
				return self.reply_text(u"谢谢您对我们的支持。在下方聊天框中输入“我有建议+您的建议+姓名+联系电话”即可。我们会认真考虑您的每一个宝贵的意见和建议，我们会在您的帮助下做得越来越好，再次感谢您的支持。")
		elif event=='subscribe':
			#print "NEW: %s" % self.fromUser
			bind_wx_user(self.fromUser, '')

			# 取得用户信息
			#info = get_info(self.fromUser)
			#print info

			#return self.reply_text(u"欢迎使用U掌柜微信服务号！")
			if setting.region_id=='003': # 华东
				ret_media = [
					(u'优鲜美味，掌上专柜！',u'',u'http://urfresh.cn/static/home/images/logo.png',u'http://app.urfresh.cn/u'),
					(u'魔都U粉会专享免单，人人有份！',u'',u'',u'http://mp.weixin.qq.com/s?__biz=MzI3OTAwODMyOQ==&mid=400211195&idx=1&sn=f3e41093c3b4594d8746fac4dd3f3106#rd'),
					(u'下载App',u'',u'http://urfresh.cn/static/home/images/download1.jpg',u'http://app.urfresh.cn/u')
				]
			if setting.region_id=='001': # 东南
				ret_media = [
					(u'轻松几步，玩转掌柜拼团',u'',u'http://img.urfresh.cn/image/product/wx_pt.jpg',u'http://mp.weixin.qq.com/s?__biz=MzA5NjUzNjQ0Ng==&mid=400701472&idx=1&sn=5b7c75fe4bc6a3a6657e05b210694645&scene=1&srcid=1117o9j4kbTC6Lr6OgsrxvFl&key=d4b25ade3662d643c704f637869cf7388cd7bd3cbf54480a99109929c68b9ba2a0c202f7e706cd057840d427d8f84be6&ascene=0&uin=MjY2ODIxNjE4MQ%3D%3D&devicetype=iMac+MacBookPro5%2C4+OSX+OSX+10.11.1+build(15B42)&version=11020201&pass_ticket=gO%2F06k1awC23cLIXWWX61aeouLubsV%2B%2BXmEVvu8quX2Dvog526AXCfBfOEDf1L6e'),
					#(u'U掌柜东南还未上线正在测试中，所显示商品为测试环境不能成单不发货，敬请期待哦～～',u'',u'',u''),
				]
			else: # 其他地区暂不提示下载
				ret_media = [
					(u'优鲜美味，掌上专柜！',u'',u'http://urfresh.cn/static/home/images/logo.png',u'http://app.urfresh.cn/u'),
					(u'魔都U粉会专享免单，人人有份！',u'',u'',u'http://mp.weixin.qq.com/s?__biz=MzI3OTAwODMyOQ==&mid=400211195&idx=1&sn=f3e41093c3b4594d8746fac4dd3f3106#rd'),
				]
			return self.reply_media(ret_media)

		elif event=='unsubscribe':
			#print "LEFT: %s" % self.fromUser
			bind_wx_user(self.fromUser, 'N/A')
		return reply_none()

	def do_process(self):
		if self.msgType=='text':
			return self.text_process()
		elif self.msgType=='event':
			return self.event_process()
		else:
			return reply_none()

class First:
	def GET(self):
#		test1='<xml><ToUserName><![CDATA[gh_96ef24d64c49]]></ToUserName>' \
#			'<FromUserName><![CDATA[ogQxxuBJi1KR_BLn86aRIKTHrcPM]]></FromUserName>' \
#			'<CreateTime>1411443827</CreateTime>' \
#			'<MsgType><![CDATA[event]]></MsgType>' \
#			'<Event><![CDATA[CLICK]]></Event>' \
#			'<EventKey><![CDATA[KAM_SNAPSHOT]]></EventKey>' \
#			'</xml>'
#		pm=PostMsg(test1)
#		return pm.do_process()

		import hashlib
		user_data=web.input(signature='', timestamp='', nonce='', echostr='')
		if '' in (user_data.signature, user_data.timestamp, user_data.nonce, user_data.echostr):
			return reply_none()

		token1='7a710d7955acb49fbf1a'  # hashlib.sha1('ilovekam').hexdigest()[5:25]
		tmp=[token1, user_data.timestamp, user_data.nonce]
		tmp.sort()
		tmp1=tmp[0]+tmp[1]+tmp[2]
		tmp2=hashlib.sha1(tmp1).hexdigest()
		#print "%s %s %s" % (tmp1, tmp2, user_data.signature)
		
		web.header("Content-Type", "text/plain") # Set the Header
		if tmp2==user_data.signature:
			return user_data.echostr
		else:
			return "fail!"

	def POST(self):
		import hashlib
		user_data=web.input(signature='', timestamp='', nonce='')
		if '' in (user_data.signature, user_data.timestamp, user_data.nonce):
			return reply_none()
		
		token1='7a710d7955acb49fbf1a'  # hashlib.sha1('ilovekam').hexdigest()[5:25]
		tmp=[token1, user_data.timestamp, user_data.nonce]
		tmp.sort()
		tmp1=tmp[0]+tmp[1]+tmp[2]
		tmp2=hashlib.sha1(tmp1).hexdigest()

		if tmp2!=user_data.signature:
			return reply_none()

		#从获取的xml构造xml dom树
		str_xml=web.data()
		
		#print str_xml
		
		pm=PostMsg(str_xml)
		return pm.do_process()

# 获取ticket
def get_ticket(force=False): # force==True 强制刷新
	if not force:
		db_ticket = db.jsapi_ticket.find_one({'region_id':setting.region_id})
		if db_ticket and int(time.time())-db_ticket.get('tick', 0)<3600:
			if db_ticket.get('ticket', '')!='':
				print db_ticket['ticket']
				return db_ticket['ticket']

	token = get_token(force)
	url='https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % token
	f=urllib.urlopen(url)
	data = f.read()
	f.close()

	print data
	t=json.loads(data)
	if t.has_key('ticket'):
		print t
		db.jsapi_ticket.update_one({'region_id':setting.region_id},
			{'$set':{'tick':int(time.time()), 'ticket':t['ticket']}},upsert=True)
		return t['ticket']
	else:
		db.jsapi_ticket.update_one({'region_id':setting.region_id},
			{'$set':{'tick':int(time.time()), 'ticket':''}},upsert=True)
		return ''

# 获取用户基本信息
def get_info(openid):
	token = get_token()
	url='https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN' % (token, openid)
	f=urllib.urlopen(url)
	data = f.read()
	f.close()

	print data
	t=json.loads(data)
	return t

# 微信入口
def get_redirect_loc(redirect_uri):
	#redirect_uri = 'http://wx-test.urfresh.cn/wx/fair'
	loc = 	'https://open.weixin.qq.com/connect/oauth2/authorize?' \
		'appid=%s&' \
		'redirect_uri=%s&' \
		'response_type=code&' \
		'scope=snsapi_base&' \
		'state=1#wechat_redirect' % (wx_appid, urllib.quote_plus(redirect_uri))
	return loc

# 店铺入口， 测试 http://wx-test.urfresh.cn/wx/fair?code=test
def init_job(code):
	if code=='':
		#return render.info('参数错误',goto='/') # info页面要做微信端优化
		#raise web.seeother('/wx/init_fair')
		return None

	if code=='test':
		openid = code
	else:
		urllib3.disable_warnings()
		http = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
		url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' \
			'appid=%s&' \
			'secret=%s&' \
			'code=%s&' \
			'grant_type=authorization_code' % \
			(wx_appid, wx_secret, code, )
		r = http.request('GET', url)
		if r.status==200:
			data = r.data
			t=json.loads(data)
			#print t
			if t.has_key('openid'):
				openid = t['openid']
			else:
				#return render.info('授权失败',goto='/')
				#raise web.seeother('/wx/init_fair')
				return None
		else:
			#raise web.seeother('/wx/init_fair')
			return None

	# 取得ticket
	ticket = get_ticket()
	if ticket=='':
		print 'get ticket fail!'
		#raise web.seeother('/wx/init_fair')
		#return None
		ticket = get_ticket(True)

	#session.login = 1
	#session.uname = ''
	#session.openid = openid
	#session.privilege = helper.PRIV_WX

	uname = ''

	# 检查用户是否已注册
	db_user = db.app_user.find_one({'openid':openid})
	if db_user==None:
		# 未注册，新建用户记录

		# 用户基本信息
		info = get_info(openid)
		if info.has_key('errcode'):
			get_ticket(True)
			info = get_info(openid)
		print info

		coupon = []
		valid = app_helper.time_str(time.time()+3600*24*10, 1) # 有效期10天 2015-11-22
		# 注册发抵用券 v3
		for i in app_helper.reginster_coupon:
			coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
		db.app_user.insert_one({
			'openid'   : openid,
			'address'  : [],
			'coupon'   : coupon, # 送优惠券
			'app_id'   : '', # 微信先注册，没有app_id
			'reg_time' : app_helper.time_str(),
			'wx_nickname'   : info.get('nickname','游客'),
			'wx_headimgurl' : info.get('headimgurl', ''),
			'wx_info'       : info,
		})
	else:
		if db_user.get('wx_headimgurl', '')=='':
			# 用户基本信息
			info = get_info(openid)
			if info.has_key('errcode'):
				get_ticket(True)
				info = get_info(openid)
			print info

			# 补充微信用户信息
			db.app_user.update_one({'openid':openid}, {'$set':{
				'wx_nickname'   : info.get('nickname','游客'),
				'wx_headimgurl' : info.get('headimgurl', ''),
				'wx_info'       : info,
			}})

		uname = db_user.get('uname','')

	# 生成 session ------------------
	import hashlib

	rand2 = app_helper.my_rand(16)
	now = time.time()
	secret_key = 'f6102bff8451236b8ca1'
	session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
	session_id = session_id.hexdigest()

	db.app_sessions.insert_one({
		'session_id' : session_id,
		'openid'     : openid,
		'ticket'     : ticket,
		'uname'      : uname,
		'login'      : 1,
		'rand'       : rand2,
		'ip'         : web.ctx.ip,
		'attime'     : now,
	})

	# 清理 session, 12小时前的微信session ---- 有隐患
	#db.app_sessions.remove({'openid':{'$exists':True},'attime':{'$lt':(now-3600*12)}})
	# 清理 session, 12小时前的未登录的session
	db.app_sessions.delete_many({'login':0,'attime':{'$lt':(now-3600*12)}})
	# 清理 session, 30天前的未使用的session
	db.app_sessions.delete_many({'attime':{'$lt':(now-3600*24*30)}})
	# -------------------------------

	print session_id, openid, uname

	render = create_render(plain=True)
	#return render.fair(session_id, uname)
	#raise web.seeother('/static/wx/fair.html?session_id=%s' % session_id)
	return session_id

# 下单入口
class InitFair:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/fair' % setting.wx_host))

class Fair: 
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_fair')
		else:
			raise web.seeother('/static/wx/fair.html?session_id=%s&region_id=001' % session_id)

# 拼团入口
class InitTuan:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/tuan' % setting.wx_host))

class Tuan: 
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_tuan')
		else:
			raise web.seeother('/static/wx/tuan.html?session_id=%s&region_id=%s' % \
				(session_id, setting.region_id))


# 我的拼团入口
class InitTuanList:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/tuan_list' % setting.wx_host))

class TuanList: 
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_tuan_list')
		else:
			raise web.seeother('/static/wx/pt_myList.html?session_id=%s&region_id=%s' % \
				(session_id, setting.region_id))


# 拼团分享入口
class InitTuanShare:
	def GET(self):
		user_data=web.input(region_id='', pt_order_id='')
		raise web.redirect(get_redirect_loc('http://%s/wx/tuan_share?region_id=%s&pt_order_id=%s' % \
			(setting.wx_host, user_data['region_id'], user_data['pt_order_id'])))

class TuanShare: 
	def GET(self):
		user_data=web.input(code='', region_id='', pt_order_id='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('http://%s/wx/tuan_share?region_id=%s&pt_order_id=%s' % \
				(setting.wx_host, user_data['region_id'], user_data['pt_order_id']))
		else:
			raise web.seeother('/static/wx/pt_active.html?session_id=%s&region_id=%s&pt_order_id=%s' % \
				(session_id, user_data['region_id'], user_data['pt_order_id']))

# 拼团详情页入口
class InitTuanDetail:
	def GET(self):
		user_data=web.input(tuan_id='')
		raise web.redirect(get_redirect_loc('http://%s/wx/tuan_detail?region_id=001&tuan_id=%s' % \
			(setting.wx_host, user_data['tuan_id'])))

class TuanDetail: 
	def GET(self):
		user_data=web.input(code='', tuan_id='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('http://%s/wx/tuan_detail?region_id=%s&tuan_id=%s' % \
				(setting.wx_host, setting.region_id, user_data['tuan_id']))
		else:
			raise web.seeother('/static/wx/pt_detail.html?session_id=%s&region_id=%s&tuan_id=%s' % \
				(session_id, setting.region_id, user_data['tuan_id']))

# 我的订单入口
class InitMyOrder:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/my_order' % setting.wx_host))

class MyOrder:
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_my_order')
		else:
			raise web.seeother('/static/wx/orderList.html?session_id=%s&region_id=%s' % \
				(session_id, setting.region_id))

# 我的地址簿入口
class InitMyAddr:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/my_address' % setting.wx_host))

class MyAddr:
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_my_address')
		else:
			raise web.seeother('/static/wx/address.html?session_id=%s&region_id=%s' % \
				(session_id, setting.region_id))

# 我的抵用券入口
class InitMyCoupon:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/my_coupon' % setting.wx_host))

class MyCoupon:
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_my_coupon')
		else:
			raise web.seeother('/static/wx/coupon.html?session_id=%s' % session_id)

# 我的余额入口
class InitMyCredit:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/my_credit' % setting.wx_host))

class MyCredit:
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_my_credit')
		else:
			raise web.seeother('/static/wx/userInfo.html?session_id=%s' % session_id)

# 绑定手机入口
class InitMyBind:
	def GET(self):
		raise web.redirect(get_redirect_loc('http://%s/wx/my_bind' % setting.wx_host))

class MyBind:
	def GET(self):
		user_data=web.input(code='')
		session_id = init_job(user_data.code)
		if session_id==None:
			raise web.seeother('/wx/init_my_bind')
		else:
			raise web.seeother('/static/wx/bind.html?session_id=%s' % session_id)


# 微信用户绑定电话
class WxPhone:
	def POST(self):
		web.header('Content-Type', 'application/json')
		#print web.input()
		param = web.input(openid='', session_id='', number='')

		if param.number=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			#print 'user_phone', uname
			if len(uname['uname'].strip())>0:
				return json.dumps({'ret' : -5, 'msg' : '已绑定手机号码，不能重复绑定'})

			number = param.number.strip()
			if len(number)<11 or (not number.isdigit()):
				return json.dumps({'ret' : -3, 'msg' : '手机号码格式错误'})

			# 随机码
			rand = app_helper.my_rand(base=1)
			register = False

	        	#发送短信验证码
	        	sms.send_rand(number, rand, register)

	        	#临时保存到phone字段
	        	db.app_user.update({'openid':uname['openid']},{'$set':{'phone':number, 'rand':rand}})

			# 返回
			return json.dumps({'ret'  : 0})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})

# 检查随机码
class WxCheckRand:
	def POST(self):
		web.header('Content-Type', 'application/json')
		#print web.input()
		param = web.input(openid='', session_id='', rand='', invitation='')

		if param.rand=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误'})

		if param.openid=='' and param.session_id=='':
			return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

		# 同时支持openid和session_id
		if param.openid!='':
			uname = app_helper.check_openid(param.openid)
		else:
			uname = app_helper.wx_logged(param.session_id)

		if uname:
			if len(uname['uname'].strip())>0:
				return json.dumps({'ret' : -5, 'msg' : '已绑定手机号码，不能重复绑定'})

			#邀请码
			if param.has_key('invitation'):
				invitation = param.invitation
				
				if db.invitation.find({'code': invitation}).count()==0: # 无效邀请码
					invitation = ''
				else:
					r = db.app_user.find_one({'openid' : uname['openid']},{'invitation':1})
				 	if r.get('invitation', '')!='': # 已填邀请码
						invitation = ''
			else:
				invitation = ''

			if invitation!='':
				# 赠送优惠券
				valid = app_helper.time_str(time.time()+3600*24*30, 1) # 有效期30天
				r = db.app_user.find_one_and_update({'openid' : uname['openid']},{
					'$set'  : {'invitation' : invitation, 'last_time' : app_helper.time_str()},
					#'$push' : {'coupon'     : (app_helper.my_rand(), valid, '5.00', 1)}, # 邀请码送5元
				})
			else:
				r = db.app_user.find_one_and_update({'openid' : uname['openid']},{
					'$set'  : {'last_time' : app_helper.time_str()}
				})

			# 检查验证码
			if param.rand.strip()!=r['rand']:
				return json.dumps({'ret' : -5, 'msg' : '短信验证码错误'})

			if len(r['address'])>0: # 应该实现：返回最近使用的地址 !!!!
				addr = {
					'id'   : r['address'][0][0],
					'name' : r['address'][0][1],
					'tel'  : r['address'][0][2],
					'addr' : r['address'][0][3],
				}
			else:
				addr = {}

			# 绑定处理
			r2 = db.app_user.find_one({'uname':r['phone']}) 
			#print r['phone'],r2
			if r2:
				# 手机号码已注册过app, 需要合并app用户和微信用户
				#print db.app_user.update_one({'openid':uname['openid']},{'$set':{
				#	'uname'   : r['phone'],
				#	'address' : r['address']+r2['address'],
				#	'coupon'  : r['coupon']+r2['coupon'],
				#	'app_id'  : r2['app_id']
				#}})
				# 使手机号帐户不能再使用
				#db.app_user.update_one({'_id':r2['_id']},{'$set' : {'uname': u'~%s' % r2['uname']}})

				print '合并到app用户'
				print db.app_user.update_one({'_id':r2['_id']},{'$set':{
					'openid'  : uname['openid'],
					'address' : r['address']+r2['address'],
					'coupon'  : r['coupon']+r2['coupon'],
				}})
				# 使微信帐户不能再使用
				db.app_user.update_one({'_id':r['_id']},{'$set' : {'openid': u'~%s' % uname['openid']}})
			else:
				# 手机号码还未注册过
				db.app_user.update_one({'openid':uname['openid']},{'$set':{'uname':r['phone']}})

			# 更新session里的uname
			db.app_sessions.update_one({'session_id':param.session_id},{'$set':{'uname':r['phone']}})

			# 返回
			return json.dumps({
				'ret'  : 0, 
				'data' : {
					'login'   : True,
					'addr'    : addr, 
				}
			})
		else:
			return json.dumps({'ret' : -4, 'msg' : '无效的openid'})


class WxSignature:
	def POST(self):
		import json, hashlib
		web.header('Content-Type', 'application/json')
		param = web.input(currUrl='',cross='')
		ticket = get_ticket()
		if ticket=='':
			# 重试一次
			ticket = get_ticket()
			if ticket=='':
				print '---------- get ticket fail!'
				#return None

		noncestr = app_helper.my_rand()
		timestamp = str(int(time.time()))
		#url = 'http://test.urfresh.cn/static/hb/001.html'
		url = param.currUrl
		string1 = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (ticket, noncestr, timestamp, url)

		print string1

		if param.cross=='yes':
			return 'jsonpcallback(%s)' % json.dumps({
				'appid'     : wx_appid,
				'timestamp' : timestamp,
				'nonceStr'  : noncestr,
				'sign'      : hashlib.sha1(string1).hexdigest(),
			})
		else:
			return json.dumps({
				'appid'     : wx_appid,
				'timestamp' : timestamp,
				'nonceStr'  : noncestr,
				'sign'      : hashlib.sha1(string1).hexdigest(),
			})

	def GET(self):
		return self.POST()

#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
