#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, sys, gc
import time, json
from bson.objectid import ObjectId
from config.url import urls
from config import setting
from config.mongosession import MongoStore
import helper

from helper import time_str
from helper import get_privilege_name
from helper import logged
from helper import create_render

db = setting.db_web  # 默认db使用web本地

app = web.application(urls, globals())
application = app.wsgifunc()

#--session---------------------------------------------------
web.config.session_parameters['cookie_name'] = 'fair_session'
web.config.session_parameters['secret_key'] = 'f6102bff8452386b8ca1'
web.config.session_parameters['timeout'] = 86400
web.config.session_parameters['ignore_expiry'] = True

if setting.debug_mode==False:
	### for production
	session = web.session.Session(app, MongoStore(db, 'sessions'), 
		initializer={'login': 0, 'privilege': 0, 'uname':'', 'uid':'', 'menu_level':''})
else:
	### for staging,
	if web.config.get('_session') is None:
		session = web.session.Session(app, MongoStore(db, 'sessions'), 
			initializer={'login': 0, 'privilege': 0, 'uname':'', 'uid':'', 'menu_level':''})
		web.config._session = session
	else:
		session = web.config._session

#----------------------------------------

# 在请求前检查helper.web_session, 调试阶段会出现此现象
def my_processor(handler): 
	if helper.web_session==None:
		print 'set helper.web_session'
		helper.set_session(session)   	
	return  handler() 

app.add_processor(my_processor)
#----------------------------------------

gc.set_threshold(300,5,5)

user_level = helper.user_level

###########################################

def my_crypt(codestr):
	import hashlib
	return hashlib.sha1("sAlT139-"+codestr).hexdigest()

class Aticle:
    def GET(self):
      render = create_render()
      user_data=web.input(id='')
      if user_data.id=='1':
	return render.article_agreement()
      elif user_data.id=='2':
	return render.article_faq()
      else:
	return render.info('不支持的文档查询！', '/')

class Login:
    def GET(self):
	if logged():
		render = create_render()
		return render.portal(session.uname, get_privilege_name())
	else:
		render = create_render()

		db_sys = db.user.find_one({'uname':'settings'})
		if db_sys==None:
			signup=0
		else:
			signup=db_sys['signup']
		return render.login(signup)

    def POST(self):
	name0, passwd = web.input().name, web.input().passwd
	
	name = name0.lower()
		
	db_user=db.user.find_one({'uname':name},{'login':1,'passwd':1,'privilege':1,'menu_level':1})
	if db_user!=None and db_user['login']!=0:
	  if db_user['passwd']==my_crypt(passwd):
		session.login = 1
		session.uname = name
		session.uid = db_user['_id']
		session.privilege = int(db_user['privilege'])
		session.menu_level = db_user['menu_level']
		raise web.seeother('/')
	
	session.login = 0
	session.privilege = 0
	session.uname=''
	render = create_render()
	return render.login_error()

class Reset:
    def GET(self):
	session.login = 0
	session.kill()
	render = create_render()
	return render.logout()

class SettingsUser:
    def _get_settings(self):
      db_user=db.user.find_one({'_id':session.uid},{'uname':1,'full_name':1})
      return db_user
	
    def GET(self):
      if logged(helper.PRIV_USER):
	render = create_render()
	return render.settings_user(session.uname, get_privilege_name(), self._get_settings())
      else:
	raise web.seeother('/')

    def POST(self):
      if logged(helper.PRIV_USER):
	render = create_render()
	#full_name = web.input().full_name
	old_pwd = web.input().old_pwd.strip()
	new_pwd = web.input().new_pwd.strip()
	new_pwd2 = web.input().new_pwd2.strip()
	
	if old_pwd!='':
	  if new_pwd=='':
	    return render.info('新密码不能为空！请重新设置。')          
	  if new_pwd!=new_pwd2:
	    return render.info('两次输入的新密码不一致！请重新设置。')
	  db_user=db.user.find_one({'_id':session.uid},{'passwd':1})
	  if my_crypt(old_pwd)==db_user['passwd']:
	    db.user.update_one({'_id':session.uid}, 
	      {'$set':{'passwd'   : my_crypt(new_pwd),
		       #'full_name': full_name
	      }})
	  else:
	    return render.info('登录密码验证失败！请重新设置。')
	#else:
	#  db.user.update_one({'_id':session.uid}, {'$set':{'full_name':full_name}})

	return render.info('成功保存！')
      else:
	raise web.seeother('/')


class ViewEvent:
	def GET(self):
		if logged(helper.PRIV_USER):
			render = create_render()
			user_data=web.input(todo='')
			
			if user_data.todo=='':
				return render.info('参数错误！')

			auth_level = -1
			if session.uname in setting.auth_user:
				auth_level = 999
			elif session.uname in setting.cs_admin:
				auth_level = 1
			
			db_todo=db.order_app.find_one({'order_id': user_data.todo})
			if db_todo!=None:
				db_shop=db.base_shop.find_one({'_id':db_todo['shop']})
				if db_todo.has_key('shop_0'):
					db_shop_0=db.base_shop.find_one({'_id':db_todo['shop_0']})
				else:
					db_shop_0={'name':'n/a'}
				return render.view_event(session.uname, get_privilege_name(), 
					user_data.todo, db_todo, int(time.time()-db_todo['e_time']), 
					auth_level, (db_shop['name'],db_shop_0['name']), 
					helper.ORDER_STATUS['APP'][db_todo['status']]) # 授权客服才能修改
			else:
				return render.info('出错，请重新提交。')
		else:
			raise web.seeother('/')

	def POST(self):
		if logged(helper.PRIV_USER):
			render = create_render()
			user_data=web.input(todo='', status='', crmtext0='', crmtext='')

			if '' in (user_data.status, user_data.todo):
				return render.info('错误的参数！')
			
			# 保存客服备注
			if user_data.status=='__CRM__':
				if user_data.crmtext0[0:3]=='n/a':
					crmt = u'%s %s\r\n%s' % (time_str(), session.uname, user_data.crmtext)
				else:
					crmt = u'%s%s %s\r\n%s' % (user_data.crmtext0, time_str(), session.uname, user_data.crmtext)
				db.order_app.update_one({'order_id':user_data.todo}, {'$set' : {'crm_text' : crmt}})
				return render.info('保存完成', goto="/view_event?todo=%s" % user_data.todo)

			# 授权客服才能修改
			auth = False
			if session.uname in setting.cs_admin:
				auth = True 
			elif session.uname in setting.auth_user:
				auth = True

			if not auth:
				return render.info('无操作权限！')

			todo_update={
				'lock'        : 0,
				'e_time'      : int(time.time())
			}				
			comment = user_data.status # history 注释

			if user_data.status not in  ['__NOP__', '__CHANGE_ADDR__']:
				todo_update['status']=user_data.status

			if user_data.status=='__CHANGE_ADDR__':
				new_address = [
					'modifed',
					user_data.addr_name,
					user_data.addr_tel,
					user_data.addr_addr,
					int(time.time()),
					{'lat':0,'lng':0},
					'',
					'',
					user_data.addr_region,
				]
				todo_update['address']=new_address
				comment = '客服修改收货信息'

			if user_data.status=='CANCEL_TO_REFUND':
				todo_update['man']=1
				todo_update['sum_to_refund']='%.2f'%float(user_data.sum_to_refund)
				comment = '客服取消订单'

			r = db.order_app.find_one_and_update({'order_id':user_data.todo}, {
				'$set'  : todo_update,
				'$push' : {'history' : (time_str(), session.uname, comment)}
			})
			#print r

			if user_data.status=='CANCEL_TO_REFUND' and r and (r.get('type') in ['TUAN','SINGLE']):
				# 如果是拼团退款，需要特别处理
				# 减少团订单人数，如果人数为零，团订单取消
				print '拼团取消订单'
				r2 = db.pt_order.find_one({'pt_order_id':r['pt_order_id']},
					{'member':1,'need':1,'status':1})
				if r2:
					if len(r2['member'])==1: # 最后一人
						print '最后一人，组团失败'
						status = 'FAIL3' # 团员取消组团失败
						member = []
					else:
						print '还有其他人，继续组团'
						status = r2['status']
						member = []
						for i in r2['member']:
							if i['openid']==r['uname']:
								continue
							else:
								member.append(i)
					r3 = db.pt_order.update_one({'pt_order_id':r['pt_order_id']},{
						'$inc'  : {'need':1},
						'$set'  : {'status':status, 'member':member},
						'$push' : {'history':(time_str(), session.uname, 'CANCEL_TO_REFUND %s'% r['uname'] )}
					})
					print r3

			return render.info('提交完成',goto="javascript:window.opener=null;window.close();",text2='关闭窗口')
		else:
			raise web.seeother('/')

class Crm:
	def GET(self):
		if logged(helper.PRIV_USER,'CRM'):
			render = create_render()
			return render.crm(session.uname, get_privilege_name())
		else:
			raise web.seeother('/')

	def POST(self):
		import re
		if logged(helper.PRIV_USER,'CRM'):
			render = create_render()
			user_data=web.input(cat='', content='')

			if user_data.cat=='' or user_data.content=='':
				return render.info('错误的参数！')
			
			condi = {
				user_data.cat:{'$in': [re.compile('^.*%s.*' % user_data.content.strip().encode('utf-8'))]},
				#'status':{'$nin':['TIMEOUT']}
			}
			db_todo = db.order_app.find(condi, 
				{'order_id':1,'uname':1,'paid_time':1,'status':1}).sort([('b_time',-1)])
			if db_todo.count()>0:
				return render.report_order(session.uname, get_privilege_name(), db_todo, helper.ORDER_STATUS)
			else:
				return render.info('未查到订单信息。')
		else:
			raise web.seeother('/')


########## Admin 功能 ####################################################

class AdminUser:
    def GET(self):
	if logged(helper.PRIV_ADMIN):
	    render = create_render()

	    users=[]            
	    db_user=db.user.find({'privilege': {'$nin': [helper.PRIV_ADMIN]}},
				{'uname':1,'privilege':1,'full_name':1}).sort([('_id',1)])
	    if db_user.count()>0:
	      for u in db_user:
		if u['uname']=='settings':
			continue
		users.append([u['uname'],u['_id'],int(u['privilege']),u['full_name']])
	    return render.user(session.uname, user_level[session.privilege], users)
	else:
	    raise web.seeother('/')


class AdminUserSetting:        
	def GET(self):
		if logged(helper.PRIV_ADMIN):
			render = create_render()
			user_data=web.input(uid='')

			if user_data.uid=='':
				return render.info('错误的参数！')  
			
			db_user=db.user.find_one({'_id':ObjectId(user_data.uid)})
			if db_user!=None:
				db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark']}}, {'name':1,'type':1})
				shops = []
				for s in db_shop:
					shops.append((s['_id'], s['name'], helper.SHOP_TYPE[s['type']]))
				return render.user_setting(session.uname, user_level[session.privilege], 
					db_user, time_str(db_user['time']), 
					get_privilege_name(db_user['privilege'],db_user['menu_level']), shops)
			else:
				return render.info('错误的参数！')  
		else:
			raise web.seeother('/')

	def POST(self):
		if logged(helper.PRIV_ADMIN):
			render = create_render()
			user_data=web.input(uid='', shop='', shop2='', full_name='', passwd='', priv=[])

			shop=''
			privilege = helper.PRIV_USER
			menu_level = '------------------------------'
			for p in user_data.priv:
				pos = helper.MENU_LEVEL[p]
				menu_level = menu_level[:pos]+'X'+menu_level[pos+1:]
				if p=='DELVERY_ORDER':
					privilege |= helper.PRIV_DELIVERY
				if p in ['DELVERY_ORDER','POS_POS','POS_INVENTORY','ONLINE_MAN',
					'POS_AUDIT','POS_REPORT','POS_PRINT_LABEL','POS_REPORT_USER']:
					if user_data.shop=='':
						return render.info('请选择门店！')
					else:
						shop = ObjectId(user_data.shop)

			# 更新数据
			update_set = {'$set':{
				'login'     : int(user_data['login']), 
				'privilege' : privilege, 
				'menu_level': menu_level,
				'full_name' : user_data['full_name'],
				'shop'      : shop
			}}

			# 如需要，更新密码
			if len(user_data['passwd'])>0:
				update_set['$set']['passwd']=my_crypt(user_data['passwd'])

			db.user.update_one({'_id':ObjectId(user_data['uid'])}, update_set)

			return render.info('成功保存！','/admin/user')
		else:
			raise web.seeother('/')

class AdminUserAdd:        
	def GET(self):
		if logged(helper.PRIV_ADMIN):
			render = create_render()
			db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark']}}, {'name':1,'type':1})
			shops = []
			for s in db_shop:
				shops.append((s['_id'], s['name'], helper.SHOP_TYPE[s['type']]))
			return render.user_new(session.uname, user_level[session.privilege],shops)
		else:
			raise web.seeother('/')

	def POST(self):
		if logged(helper.PRIV_ADMIN):
			render = create_render()
			user_data=web.input(uname='', login='0', passwd='', shop='', shop2='', full_name='', priv=[])
			print user_data

			if user_data.uname=='':
				return render.info('用户名不能为空！')  
			
			db_user=db.user.find_one({'uname': user_data['uname']})
			if db_user==None:
				shop = ''
				privilege = helper.PRIV_USER
				menu_level = '------------------------------'
				for p in user_data.priv:
					pos = helper.MENU_LEVEL[p]
					menu_level = menu_level[:pos]+'X'+menu_level[pos+1:]
					if p=='DELVERY_ORDER':
						privilege |= helper.PRIV_DELIVERY
					if p in ['DELVERY_ORDER','POS_POS','POS_INVENTORY','ONLINE_MAN',
						'POS_AUDIT','POS_REPORT','POS_PRINT_LABEL','POS_REPORT_USER']:
						if user_data.shop=='':
							return render.info('请选择门店！')
						else:
							shop = ObjectId(user_data.shop)

				db.user.insert_one({
					'login'     : int(user_data['login']),
					'uname'     : user_data['uname'],
					'full_name' : user_data['full_name'],
					'privilege' : privilege,
					'menu_level': menu_level,
					'shop'      : shop,
					'passwd'    : my_crypt(user_data['passwd']),
					'time'      : time.time()  # 注册时间
				})
				return render.info('成功保存！','/admin/user')
			else:
				return render.info('用户名已存在！请修改后重新添加。')
		else:
			raise web.seeother('/')

class AdminSysSetting:        
    def GET(self):
      if logged(helper.PRIV_ADMIN):
	render = create_render()
	
	db_sys=db.user.find_one({'uname':'settings'})
	if db_sys!=None:
	  return render.sys_setting(session.uname, user_level[session.privilege], db_sys)
	else:
	  db.user.insert_one({'uname':'settings','signup':0,'login':0,
		'pk_count':1,'wt_count':1,'sa_count':1})
	  return render.info('如果是新系统，请重新进入此界面。','/')  
      else:
	raise web.seeother('/')

    def POST(self):
      if logged(helper.PRIV_ADMIN):
	render = create_render()
	user_data=web.input(signup='0', pk_count='1', wt_count='1', sa_count='1')
  
	db.user.update_one({'uname':'settings'},{'$set':{
	    'pk_count': int(user_data['pk_count']),
	    'wt_count': int(user_data['wt_count']),
	    'sa_count': int(user_data['sa_count']),
	}})

	return render.info('成功保存！','/admin/sys_setting')
      else:
	raise web.seeother('/')

class AdminSelfSetting:
    def _get_settings(self):
      db_user=db.user.find_one({'_id':session.uid})
      return db_user
	
    def GET(self):
      #print web.ctx
      if logged(helper.PRIV_ADMIN):
	render = create_render()
	return render.self_setting(session.uname, user_level[session.privilege], self._get_settings())
      else:
	raise web.seeother('/')

    def POST(self):
      if logged(helper.PRIV_ADMIN):
	render = create_render()
	old_pwd = web.input().old_pwd.strip()
	new_pwd = web.input().new_pwd.strip()
	new_pwd2 = web.input().new_pwd2.strip()
	
	if old_pwd!='':
	  if new_pwd=='':
	    return render.info('新密码不能为空！请重新设置。')
	  if new_pwd!=new_pwd2:
	    return render.info('两次输入的新密码不一致！请重新设置。')
	  db_user=db.user.find_one({'_id':session.uid},{'passwd':1})
	  if my_crypt(old_pwd)==db_user['passwd']:
	    db.user.update_one({'_id':session.uid}, {'$set':{'passwd':my_crypt(new_pwd)}})
	    return render.info('成功保存！','/')
	  else:
	    return render.info('登录密码验证失败！请重新设置。')
	else:
	  return render.info('未做任何修改。')
      else:
	raise web.seeother('/')

class AdminStatus: 
    def GET(self):
      import os
      
      if logged(helper.PRIV_ADMIN):
	render = create_render()
		
	uptime=os.popen('uptime').readlines()
	takit=os.popen('pgrep -f "uwsgi_fair.sock"').readlines()
	error_log=os.popen('tail %s/error.log' % setting.logs_path).readlines()
	uwsgi_log=os.popen('tail %s/uwsgi_fair.log' % setting.logs_path).readlines()
	processor_log=os.popen('tail %s/processor.log' % setting.logs_path).readlines()
	df_data=os.popen('df -h').readlines()

	return render.status(session.uname, user_level[session.privilege],
	    {
	      'uptime'       :  uptime,
	      'takit'        :  takit,
	      'error_log'    :  error_log,
	      'uwsgi_log'    :  uwsgi_log,
	      'process_log'  :  processor_log,
	      'df_data'      :  df_data,
	    })
      else:
	raise web.seeother('/')

class AdminData: 
    def GET(self):
      if logged(helper.PRIV_ADMIN):
	render = create_render()
	
	db_active=db.user.find({'$and': [{'login'     : 1},
					 {'privilege' : helper.PRIV_USER},
					]},
				   {'_id':1}).count()
	db_nonactive=db.user.find({'$and': [{'login'     : 0},
					 {'privilege' : helper.PRIV_USER},
					]},
				   {'_id':1}).count()
	db_admin=db.user.find({'privilege' : helper.PRIV_ADMIN}, {'_id':1}).count()

	db_sessions=db.sessions.find({}, {'_id':1}).count()
	db_device=db.device.find({}, {'_id':1}).count()
	db_todo=db.todo.find({}, {'_id':1}).count()
	db_sleep=db.todo.find({'status':'SLEEP'}, {'_id':1}).count()
	db_lock=db.todo.find({'lock':1}, {'_id':1}).count()
	db_thread=db.thread.find({}).sort([('tname',1)])
	idle_time = []
	for t in db_thread:
		idle_time.append(t)

	return render.data(session.uname, user_level[session.privilege],
	    {
	      'active'       :  db_active,
	      'nonactive'    :  db_nonactive,
	      'admin'        :  db_admin,
	      'sessions'     :  db_sessions,
	      'device'       :  db_device,
	      'todo'         :  db_todo,
	      'sleep'        :  db_sleep,
	      'lock'         :  db_lock,
	      'idle_time'    :  idle_time,
	    })
      else:
	raise web.seeother('/')


#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
