#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, json

import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/image')

# 图片上传 -------------------
def write_image(image, data):
	to_path='%s/%s' % (setting.image_store_path, image[:2])
	if not os.path.exists(to_path):
		os.makedirs(to_path)
		os.chmod(to_path, 0777)
	h=open('%s/%s' % (to_path, image), 'wb')
	h.write(data)
	h.close()

class handler: # PlatImage
	def GET(self):
		if helper.logged(helper.PRIV_USER):
			render = helper.create_render()
			return render.image(helper.get_session_uname(), helper.get_privilege_name())
		else:
			raise web.seeother('/')

	def POST(self):
		web.header("Content-Type", "application/json")
		if helper.logged(helper.PRIV_USER):
			images = web.webapi.rawinput().get('images') # 支持多个文件同时上传
			if not isinstance(images, list): 
				images = [images]
			
			result = {'ret':0, 'image': []}
			for img in images:
				#print img.filename, len(img.value)
				image_name = helper.my_rand(10) + os.path.splitext(img.filename)[1]
				if db.base_image.find({'image' : image_name}).count()>0:
					image_name = helper.my_rand(10) # 两次重复的概率很小了
				db.base_image.insert_one({
					'image' : image_name,
					'file'  : img.filename,
					'size'  : len(img.value),
					'refer' : 0,
				})
				write_image(image_name, img.value)
				result['image'].append(image_name)
			return json.dumps(result)

		else:
			return json.dumps({'ret':-1})
