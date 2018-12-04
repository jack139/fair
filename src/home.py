#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json
#import os, sys, gc
from config import setting
import helper

db = setting.db_web

urls = [
	'/',		'Home',
	'/u',		'AppHome',
	'/u/',		'AppHome',
	'/u/meituan',	'AppMeituan',
	'/u/eleme',	'AppEleme',
	'/u/record',	'AppRecord',
]

app = web.application(urls, globals())
application = app.wsgifunc()

#gc.set_threshold(300,5,5)

class Home:
	def GET(self):
		raise web.seeother('/static/home/index.html')

class AppHome:
	def GET(self):
		#print web.ctx.environ.get('HTTP_USER_AGENT')
		render = web.template.render('templates/home')
		return render.app('urfresh')

class AppMeituan:
	def GET(self):
		render = web.template.render('templates/home')
		return render.app('meituan')

class AppEleme:
	def GET(self):
		render = web.template.render('templates/home')
		return render.app('eleme')

class AppRecord:
	def POST(self):
		web.header("Content-Type", "application/json")
		user_data=web.input(app_type='',source='')
		db.download_record.insert_one({
			'date'     : helper.time_str(),
			'app_type' : user_data['app_type'],
			'source'   : user_data['source'],
		})
		return json.dumps({'ret' : 0})

#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
