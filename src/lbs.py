#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 百度LBS api，使用 urllib3
#
import httphelper3
import json
from config import setting

db = setting.db_web

## ---- 有关参数  ---------------------------------------------------

# 软件密钥
appkey      = 'ptQgYEMDQl38IqHMbz0p13G5'
# API url
geocoding_url = 'http://api.map.baidu.com/geocoder/v2/'
geoconv_url = 'http://api.map.baidu.com/geoconv/v1/'

#
# --------------- API to Baidu LBS --------------------------------------------------
#


# 返回结果中的data域
def process_result(data, item=None):
	try:
		data2=json.loads(data)
		print data2
	except ValueError:
		print data
		return (httphelper3.E_JSON, 'load json fail.')

	if data2['status']==0:
		if item:
			return (httphelper3.E_OK, data2.get('result').get(item))
		else:
			return (httphelper3.E_OK, data2.get('result'))
	else:
		return (httphelper3.E_DATA, data2)

def process_result2(data):
	try:
		data2=json.loads(data)
		print data2
	except ValueError:
		print data
		return (httphelper3.E_JSON, 'load json fail.')

	if data2['status']==0:
		return (httphelper3.E_OK, data2.get('result')) # 直接返回result
	else:
		return (httphelper3.E_DATA, data2)

# 地址 --> 经纬度
def addr_to_loc(address, city='上海市', return_item='location'): 
	# POST
	print 'addr_to_loc()'

	# 特定地址找不到的问题
	if '梅花路' in address:
		address = address.replace('梅花路', '锦绣路梅花路')
	# 截断
	if '号' in address:
		address2 = address.split('号')[0]+'号'
	elif '弄' in address:
		address2 = address.split('弄')[0]+'号'
	elif '路' in address:
		address2 = address.split('路')[0]+'路'
	elif '中心' in address:
		address2 = address.split('中心')[0]+'中心'
	elif '大厦' in address:
		address2 = address.split('大厦')[0]+'大厦'
	elif '广场' in address:
		address2 = address.split('广场')[0]+'广场'
	else:
		address2 = address
	address2 = address2.replace('弄','号')
	print address, address2
	body = {'ak': appkey, 'output': 'json', 'address': address2, 'city': city}
	data = httphelper3.http_post('webpy', geocoding_url, body, json=False)
	if data==None:
		return (httphelper3.E_QUERY, 'query no return')
	else:
		ret, data2 = process_result2(data)
		if ret<0:
			return (ret, data2)
		print data2['level'].encode('utf-8')
		if (data2['level'] in [u'道路', u'交叉路口', u'商务大厦', u'地产小区']) or \
			data2['confidence']>=90 or \
			(data2['confidence']>=70 and data2['level'] not in [u'餐饮']) or \
			(data2['precise']==1 and data2['confidence']>=50 and data2['level'] not in [u'餐饮']):
			# 可信度其他大于75，道路允许大于50，否则按出错处理
			return (ret, data2[return_item])
		else:
			#db.addr_fail.insert_one({'addr':address, 'addr2':address2, 'data2':data2})
			db.addr_fail.update_one({'addr':address}, {'$set':{
				'addr':address, 'addr2':address2, 'data2':data2
			}}, upsert=True)
			return (httphelper3.E_DATA, data2)

# 经纬度 --> 地址
def loc_to_addr(lat, lng, coordtype='bd09ll', return_item='formatted_address'): # 默认百度坐标，GPS坐标： wgs84ll
	# POST
	print 'loc_to_addr()'
	body = {'ak': appkey, 'output': 'json', 'coordtype':coordtype, 'location': '%.10f,%.10f' % (lat, lng)}
	data = httphelper3.http_post('webpy', geocoding_url, body, json=False)
	if data==None:
		return (httphelper3.E_QUERY, 'query no return')
	else:
		return process_result(data, return_item)

# 坐标转换
# 1 GPS设备, 3 google地图、soso地图、aliyun地图、mapabc地图和amap地图, 5 百度地图, 7 mapbar地图, 8 51地图
def geo_convert(x, y, type_from=1): 
	# POST
	print 'geoconvert()'
	if x<y:
		lat = x
		lng = y
	else:
		lat = y
		lng = x
	body = {'ak': appkey, 'output': 'json', 'from':type_from, 'to':5, 'coords': '%.10f,%.10f' % (lng, lat)}
	data = httphelper3.http_post('webpy', geoconv_url, body, json=False)
	if data==None:
		return (httphelper3.E_QUERY, 'query no return')
	else:
		# (0, [{u'y': 31.21201137465, u'x': 121.60080066623}])
		#print data
		return process_result(data)

# 计算两坐标的距离
def geo_distance(lat1, lng1, lat2, lng2):
	import math
	R = 6370996.81
	d = R*math.acos(math.cos(lat1*math.pi/180)*math.cos(lat2*math.pi/180)*math.cos(lng1*math.pi/180-lng2*math.pi/180)
		+math.sin(lat1*math.pi/180)*math.sin(lat2*math.pi/180))
	return round(d/1000,2)

# 卷绕法计算点是否在封闭多边形内
# p=(x,y)
def isLeft(p0, p1, p2):
	return ( (p1[0]-p0[0])*(p2[1]-p0[1]) - (p2[0]-p0[0])*(p1[1]-p0[1]) )

# p 点， poly 面 ［p0, p1, p2, ..., p0］
# 返回0不在多边形内，返回非0在多边形内
def wn_PnPoly(p, poly):
	wn = 0
	for i in xrange(len(poly)-1):
		if poly[i][1] <= p[1]:
			if poly[i+1][1] > p[1]:
				if isLeft(poly[i], poly[i+1], p)>0:
					wn += 1
		else:
			if poly[i+1][1] <= p[1]:
				if isLeft(poly[i], poly[i+1], p)<0:
					wn -= 1
	return wn


# 检查点是否在多边形区域内
def check_in_poly(point, poly): # point=(lat, lng)  poly=[]
	# 多边形检查
	#poly = db_shop.get('poly_xy', [])
	if len(poly)==0: # 没有多边形数据
		print "缺少多边形数据!"
		return False
	if wn_PnPoly(point, poly)!=0:
		print '可送货'
		return True
	else:
		print '不在送货范围'
		#print poly
		return False

# 匹配地址和门店
def locate_shop(point): # point=(lat, lng) # 返回：( (_id, name, address), {lat: x, lng: y} )
	poly_shop = None # 多边形匹配
	db_shop = db.base_shop.find({'type':{'$in':['chain','store','dark']}})
	for s in db_shop:
		if s.get('app_shop', 1)==0: # 忽略不支持线上销售的店
			continue
		# 多边形检查
		poly = s.get('poly_xy', [])
		if len(poly)==0: # 没有多边形数据
			print "缺少多边形数据!"
			continue
		if wn_PnPoly(point, poly)!=0:
			print 'bingo! poly_shop', s['name'].encode('utf-8')
			poly_shop=(s['_id'],s['name'],s['address'])
			loc_shop={'lat': poly[0][0], 'lng': poly[0][1]} # 用多边形第一个点算距离
			break

	if poly_shop==None:
		print '不在配送范围内'
		return (None, None)
	else:
		return (poly_shop, loc_shop)
