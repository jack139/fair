#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import web
import time, datetime, os
import urllib2
import re
from config import setting
from app_helper import CATEGORY

db = setting.db_web

web_session = None

ISOTIMEFORMAT=['%Y-%m-%d %X', '%Y-%m-%d', '%Y%m%d']

reg_b = re.compile(r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows (ce|phone)|xda|xiino", re.I|re.M)
reg_v = re.compile(r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-", re.I|re.M)

def time_str(t=None, format=0):
    return time.strftime(ISOTIMEFORMAT[format], time.localtime(t))

def detect_mobile():
  if web.ctx.has_key('environ'):
    user_agent = web.ctx.environ['HTTP_USER_AGENT']
    b = reg_b.search(user_agent)
    v = reg_v.search(user_agent[0:4])
    if b or v:
      return True
  return False

def validateEmail(email):
    if len(email) > 7:
      if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
	return 1
    return 0

##############################################

# 用户等级
#PRIV_SERVICE  = 0b10000000  # 128
PRIV_USER     = 0b01000000  # 64
#PRIV_SHOP     = 0b00100000  # 32
PRIV_DELIVERY = 0b00010000  # 16 # 要保留，区别后台用户与配送员
PRIV_ADMIN    = 0b00001000  # 8
PRIV_WX       = 0b00000100  # 4
#PRIV_ORDER    = 0b00000010  # 2
#PRIV_WHOUSE   = 0b00000001  # 1
PRIV_VISITOR  = 0b00000000  # 0

# 菜单权限
MENU_LEVEL = {
	'PLAT_SKU_STORE' : 0, 	# SKU管理
	'PLAT_BASE_SKU'  : 1, 	# SKU基础资料
	'PLAT_BASE_SHOP' : 2, 	# 站点基础资料
	'STOCK_INVENTORY': 3, 	# 库存管理
	'STOCK_ORDER'    : 4, 	# 工单管理
	'POS_POS'        : 5, 	# 销货
	'POS_INVENTORY'  : 6, 	# 店内库存
	'ONLINE_MAN'     : 7, 	# 线上订单
	'POS_AUDIT'      : 8, 	# 盘点
	'POS_REPORT'     : 9, 	# 销货统计
	'POS_PRINT_LABEL': 10, 	# 打印标签
	'POS_REPORT_USER': 11, 	# 打印班组统计
	'CRM'            : 12, 	# 订单查询
	'DELVERY_ORDER'  : 13, 	# 快递员UI
	'REPORT_REPORT1' : 14,  # 报表
	'REPORT_REPORT2' : 15,  # 报表
	'REPORT_QUERY'   : 16,  # 手工查询
	'APP_PUSH'       : 17,  # 推送app消息
	'REPORT_VOICE'   : 18,  # 客户反馈
	'BI_REPORT'      : 19,  # BI报表
	'PLAT_PT_STORE'  : 20,  # 拼团活动管理
	'BATCH_JOB'      : 21,  # 批量处理订单
}

user_level = {
	PRIV_VISITOR  : '访客',
	PRIV_ADMIN    : '管理员',
	PRIV_USER     : '平台管理', 
	#PRIV_ORDER    : '订单管理', 
	#PRIV_WHOUSE   : '仓储管理', 
	#PRIV_SHOP     : '门店POS',
	PRIV_DELIVERY : '快递员',
	#PRIV_SERVICE  : '客服',
}

#################


UNIT_TYPE = {
	'g'      : '克',
	'jin'    : '斤',
	'kg'     : '公斤',
#	'lb'     : '磅',
#	'L'      : '升',
#	'ml'     : '毫升',
	'pc1'    : '个',
	'pc2'    : '件',
	'pc3'    : '只',
	'pc4'    : '条',
#	'dozen'  : '打', 
	'box'    : '盒',
	'pack'   : '箱',
#	'bottle' : '瓶',
}

SHOP_TYPE = {
	'chain'   : '直营店',
	'store'   : '加盟店',
	'counter' : '专柜',
	'dark'    : '暗店',
	'house'   : '仓库',
	'branch'  : '分拨中心',
	'truck'   : '移动货车',
}


ORDER_STATUS = {
	'SEND' : { # 发货单
		'name'    : '发货单',
		'WAIT'    : '等待采购处理',
		'ONSHOP'  : '货物在途',
		'CONFIRM' : '确认已收货',
		'RETURN'  : '退货',
		'FINISH'  : '结束',
	},
	'BOOK' : { # 订货单
		'name'    : '订货单',
		'WAIT'    : '等待采购处理',
		'ONSHOP'  : '货物在途',
		'CONFIRM' : '确认已收货',
		'ORDERED' : '已出发货单',
		'REFUSE'  : '拒绝',
		'FINISH'  : '结束',
	},
	'WORK' : { # 加工单
		'name'   : '加工单',
		'WAIT'   : '等待处理',
		'WORK'   : '加工中',
		'WAITIN' : '等待入库',
		'FINISH' : '结束',
	},
	'APP' : { # 线上订单
		'name'     : '线上订单',
		'DUE'      : '待支付',
		'PREPAID'  : '付款确认中',
		'PAID'     : '已付款',
		'DISPATCH' : '已拣货，待配送',
		'ONROAD'   : '配送中',
		'COMPLETE' : '配送完成',
		'FINISH'   : '已完成',
		'CANCEL'   : '已取消',
		'TIMEOUT'  : '已过付款期限',
		'GAP'      : '缺货处理',
		'REFUND'   : '已退款',
		'FAIL'     : '配送失败',
		'CANCEL1'  : '第3方取消订单1',
		'CANCEL2'  : '第3方取消订单2',
		'CANCEL3'  : '第3方取消订单3',
		'CANCEL4'  : '第3方取消订单4',
		# 拼团使用
		'PAID_AND_WAIT'    : '等待成团',
		'FAIL_TO_REFUND'   : '拼团失败退款中',
		'CANCEL_TO_REFUND' : '订单取消退款中'
	}
}

PT_REGION = {
	'000' : '测试',
	'001' : '东南',
	'002' : '华北',
	'003' : '华东',
}

#CATEGORY = {
#	'001' : '新鲜水果', #'掌柜优选',
#	'002' : '缤纷饮料', #'新鲜水果',
#	'003' : '休闲零食', #'水灵蔬菜',
#	'004' : '单人套餐', #'无肉不欢',
#	'005' : '多人套餐', #'极鲜水货',
#	'006' : '整箱预售', #'天下粮仓',
#	'007' : '夜市促销', #'零食小吃',
#}

# 为子文件传递session ---------------------

def set_session(s):
	global web_session
	web_session = s

def get_session_uname():
	return web_session.uname

#----------------------------------------

is_mobi=''  # '' - 普通请求，'M' - html5请求

def get_privilege_name(privilege=None, menu_level=None):
	if privilege==None:
		privilege = web_session.privilege

	name = ['?']
	p = int(privilege)
	if p==PRIV_ADMIN:
		return user_level[PRIV_ADMIN]
	if p&(PRIV_USER|PRIV_DELIVERY):
		if menu_level==None:
			menu_level = web_session.menu_level  # '----X--X----XXX---'
		for k in MENU_LEVEL.keys():
			if menu_level[MENU_LEVEL[k]]=='X':
				name.append(k)
	return name

def my_rand(n=5):
	import random
	return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz') for ch in range(n)])

def logged(privilege = -1, menu_level=None):
	if web_session.login==1:
		if privilege == -1:  # 只检查login, 不检查权限
			return True
		else:
			if int(web_session.privilege) & privilege: # 检查特定权限
				if menu_level:
					# 检查菜单权限
					if web_session.menu_level[MENU_LEVEL[menu_level]]=='X':
						return True
					else:
						return False
				else:
					return True
			else:
				return False
	else:
		return False

def create_render(plain=False, globals={}):
	global is_mobi
	# check mobile
	if detect_mobile():
		is_mobi='M'
	else:
		is_mobi=''
    
	print 'is_mobi', is_mobi

	if plain: layout=None
	else: layout='layout'

	privilege = web_session.privilege

	if logged():
		if privilege == PRIV_WX:
			render = web.template.render('templates/wx', base=layout, globals=globals)
		elif privilege == PRIV_ADMIN:
			render = web.template.render('templates/admin', base=layout, globals=globals)
		elif privilege&PRIV_DELIVERY:
			print 'delivery'
			render = web.template.render('templates/user%s' % is_mobi, base=layout, globals=globals)
		elif privilege&PRIV_USER:
			print 'user'
			render = web.template.render('templates/user', base=layout, globals=globals)
		else:
			render = web.template.render('templates/visitor%s' % is_mobi, base=layout, globals=globals)
	else:
		render = web.template.render('templates/visitor%s' % is_mobi, base=layout)

	# to find memory leak
	#_unreachable = gc.collect()
	#print 'Unreachable object: %d' % _unreachable
	#print 'Garbage object num: %s' % str(gc.garbage)

	return render


## 数据库操作

#--- 取得指定sku的库存总数
def get_inventory(sku, shop=None):
	
	if shop: # 指定站点时，把门店价格一起带出来
		db_invent=db.inventory.find_one({'sku':sku, 'shop':shop},{'num':1, 'price':1})
		if db_invent:
			return (db_invent['num'], db_invent['price'])
		else:
			return (0, '0.00')
	else:
		db_invent=db.inventory.find({'sku':sku},{'num':1})
		total = 0
		for i in db_invent:
			total += i['num']
		return total
	
#-- 取得shop的信息

def get_shop(shop):
	return db.base_shop.find_one({'_id':shop},{'name':1, 'type':1})

#-- 取得uid的shop
def get_shop_by_uid():
	return db.user.find_one({'_id' : web_session.uid},{'shop':1})


# elm 修改库存
def elm_modify_num(shop_id, product_id):
	from app_helper import elm_modify_num as elm_modify_num_app
	elm_modify_num_app(shop_id, product_id)

