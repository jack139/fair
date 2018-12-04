#!/usr/local/bin/python
#-*- coding:utf-8 -*-

import httplib, urllib, json, time
from config import setting

db = setting.db_web

#version = "v1"
#通用短信接口的URI
#sms_send_uri = "/" + version + "/sms/send.json"
#api_key
apikey = "e105ead8467f1d4c99ff15225c820668"

# 通用接口发短信	
def send_sms(text, mobile): # 云片网
	params = urllib.urlencode({'apikey': apikey, 'text': text, 'mobile':mobile})
	headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
	conn = httplib.HTTPConnection('yunpian.com', port=80, timeout=60)
	conn.request("POST", '/v1/sms/send.json', params, headers)
	response = conn.getresponse()
	response_str = response.read()
	conn.close()
	return response_str

def send_sms2(text, mobile): # 企信通
	url = '/smspost_utf8/sendbyid.aspx?username=jack139&password=wobuzhidaomima&mobile=%s&content=%s' % \
		(mobile.encode('utf-8'), text)
	#print url
	conn = httplib.HTTPConnection('www.gysoft.cn', port=80, timeout=60)
	conn.request("GET", url)
	response = conn.getresponse()
	response_str = response.read()
	conn.close()
	return response_str

def send_sms3(text, mobile): # 云信留客
	# http://h.1069106.com:1210/services/msgsend.asmx/SendMsg
	url = '/Services/MsgSend.asmx/SendMsg?userCode=JLXX&userPass=JLXX789&DesNo=%s&Msg=%s&Channel=' % \
		(mobile.encode('utf-8'), text)
	#print url
	conn = httplib.HTTPConnection('h.1069106.com', port=1210, timeout=60)
	conn.request('GET', url)
	response = conn.getresponse()
	response_str = response.read()
	conn.close()
	return response_str

# 检查发送频率
# 每小时可发送 10 次，每次间隔大于1分钟
def check_send_freq(mobile): 
	tick = int(time.time())
	r = db.sms_sent_log.find_one({'mobile':mobile})
	if r==None: 
		# 没发过
		db.sms_sent_log.insert_one({
			'mobile'    : mobile,
			'last_t'    : tick, # 最近一次 tick
			'in_hour'   : tick, # 1小时计数 tick
			'n_in_hour' : 1,  # 1小时计数
		})
	else:
		if tick-r['last_t']<60: # 每次间隔大于1分钟
			print '短信 -------> ', mobile, '------> 1分钟内多次！'
			return False
		if tick-r['in_hour']<3600 and r['n_in_hour']>=10: # 1小时内发生不超过10次
			print '短信 -------> ', mobile, '------> 1小时内超过10次！'
			return False
		# 更新时间记录
		db.sms_sent_log.update_one({'mobile' : mobile},{'$set':{
			'last_t' : tick,
			'in_hour' : tick if tick-r['in_hour']>3600 else r['in_hour'],
			'n_in_hour' : 1 if tick-r['in_hour']>3600 else (r['n_in_hour']+1),
		}})
	return True

# 发验证码
def send_rand(mobile, rand, register=False):
	# 检查发送频率
	if not check_send_freq(mobile): 
		return None

	print '短信 -------> ', mobile, '------>', rand
	# 移动号码 ('134','135','136','137','138','139','150','151','152','157','158','159','187','188')

	if register:
		text = "感谢您注册U掌柜，您的验证码是%s【U掌柜】" % rand
	else:
		text = "您的验证码是%s。如非本人操作，请忽略本短信【U掌柜】" % rand
	r = send_sms3(text, mobile) # 云信
	print r
	return r

	'''
	if mobile[:3] in ('135','136'):
		if register:
			text = "感谢您注册U掌柜，您的验证码是%s【U掌柜】" % rand
		else:
			text = "您的验证码是%s。如非本人操作，请忽略本短信【U掌柜】" % rand
		r = send_sms3(text, mobile) # 云信
		print r
		return r
	elif mobile[:3] in ('185','134','137','138','139','150','151','152','157','158','159','187','188'):
		if register:
			text = "感谢您注册U掌柜，您的验证码是%s【U掌柜】" % rand
		else:
			text = "您的验证码是%s。如非本人操作，请忽略本短信【U掌柜】" % rand
		r = send_sms3(text, mobile) # 云信
		print r
		return r
	else:
		if register:
			text = "【U掌柜】感谢您注册U掌柜，您的验证码是%s" % rand
		else:
			text = "【U掌柜】您的验证码是%s。如非本人操作，请忽略本短信" % rand
		#调用通用接口发短信
		r = send_sms(text, mobile) # 云片
		print r

		r2 = json.loads(r)
		if r2['code']==0:
			return r2['result']
		else:
			return None
	'''