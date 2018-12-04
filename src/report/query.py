#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/report/query')

# - 手工查询 －－－－－－－－－－－
class handler:        #class PosReport:
	def GET(self):
		if helper.logged(helper.PRIV_USER,'REPORT_QUERY'):
			render = helper.create_render()
			return render.report_query(helper.get_session_uname(), helper.get_privilege_name())
		else:
			raise web.seeother('/')

	def POST(self):
		if helper.logged(helper.PRIV_USER,'REPORT_QUERY'):
			render = helper.create_render()
			param = web.input(db='', query='', projection='', ret_type='table')

			db_name = param.db.strip()
			query = eval(param.query.strip())
			projection = eval(param.projection.strip())

			if '' in (db_name, query, projection):
				return render.info('db_name不能为空！')  

			if projection=={}:
				db_query = db[db_name].find(query)
			else:
				db_query = db[db_name].find(query, projection)
			table = []
			if db_query.count()>5000:
				return render.info('数据太多，请设置查询条件！')  
			elif db_query.count()>0:
				header = db_query[0].keys()
				for i in db_query:
					row = []
					for j in header:
						c = i.get(j,'')
						if type(c)!=type(''):
							c = str(c)
						else:
							c = c.encode('utf-8')
						row.append(c)
					table.append(row)

				if param.ret_type=='table':
					# 返回table
					return render.report_query_r(helper.get_session_uname(), helper.get_privilege_name(), 
						header, table)
				else:
					# 返回csv格式文本
					web.header('Content-Type', 'text/plain')
					ret_txt=','.join(header)+'\n'
					for i in table:
						ret_txt = ret_txt + ','.join(i) + '\n'
					return ret_txt
			else:
				return render.info('无数据返回！')  
		else:
			raise web.seeother('/')

