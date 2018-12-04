#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 后台服务进程，后台运行 - 多线程版本
#
# 1. 检查todo，是否有event
# 2. 按event和status处理
#
# ！！！需改进：
#		对中断的处理：kill信号
#
import sys, time, gc #, os
import threading
import json, random
import helper #, stations
#import httphelper3, sjrandhelper3, sjrandhelper
from config import setting

db = setting.db_web

#
# 目前需手工处理的status: SJRAND, SJRAND_P, PAY
#

def waring(s): # 输出到stderr
	sys.stderr.write(s)

def main_loop(tname):
	# 取事件队列，取得入口status
	db_todo0=db.todo.find_one_and_update(
		{'$and': [
				{'lock' : 0},
				{'man'  : 0},
				{'e_time' : {'$lt': int(time.time())}}, # 不执行未来的事件
				{'$or'  : [
						{'status':{'$nin':['FINISH','COMPLETE']}},
						{'return': 1}
					]
				}
			]
		},
		{'$set': {'lock':1}},
		{'status':1},
		sort = [('e_time',1)],
	)

	if db_todo0==None: # 队列中没有要处理的event
		#sys.stdout.write('.')
		hh = time.localtime().tm_hour
		idle_time = random.randint(1,5) # 随机休息1-5秒
		
		if hh==5: # 5点统计清零
			db.thread.update_one({'tname':tname},{'$set':{
				'0':0,   '1':0,  '2':0,  '3':0,  '4':0,  '5':0,  '6':0,  '7':0,
				'8':0,   '9':0, '10':0, '11':0, '12':0, '13':0, '14':0, '15':0,
				'16':0, '17':0, '18':0, '19':0, '20':0, '21':0, '22':0, '23':0,				
			}}, upsert=True)
		else:
			db.thread.update_one({'tname':tname},{'$inc':{str(hh):idle_time}},upsert=True)

		time.sleep(idle_time) 
		return

	#print "%s: %s - enter loop ...." % (tname helper.time_str())

	while 1: # 连续处理status

		# 取得todo的实际数据
		db_todo=db.todo.find_one({'_id':db_todo0['_id']})
		
		process_time = helper.time_str()
	
		# 处理事件
		print '%s: %s - %s %s' % (tname, process_time, str(db_todo['_id']), db_todo['status'])
	
		todo_update={ # 不再处理, 默认出错返回
			'status'  : 'FAIL',
			'man'     : 0,
			#'lock'    : 0,
		}
		DELAY=0

		while 1: # 方便跳出
			# 
			if db_todo['status']!='QUERY': 
				todo_update['comment']='1|QUERY|12306调整，暂时不能提供服务。'
				todo_update['status']='FINISH'
				break
	
			# 开始处理status
			elif db_todo['status']=='SLEEP': # 20150404
				# 检查打码队列
				sjrand_queue = db.todo.find({'status':{'$in':['SJRAND','SJRAND_P','SJRAND3_RESULT']}}).count()
				if sjrand_queue >= SJRAND_MAX:
					# 队列太大，按紧急程度安排等候
					todo_update['status']='SLEEP'
					if db_todo.has_key('orderTick'): # 兼容旧数据 20150426
						if db_todo['e_time']-db_todo['orderTick']>600:
							# 处理时间超过5分钟的，优先进入队列处理
							DELAY = 3
						else:
							# 其他等待15秒
							DELAY = 15
					else:
						DELAY = 15
				else:
					# 跳转到next_status 20150406
					todo_update['status']=db_todo['next_status'].encode('utf-8')
					todo_update['next_status']=''

			elif db_todo['status']=='NO_TICKET':
				# 手工无票处理
				todo_update['comment']='1|NO_TICKET|无票'
				break
				
		
			elif db_todo['status']=='FAIL':
				if db_todo['event'] in ('ORDER_UI', 'ORDER_API'):
					# UI事件处理，到此结束
					None
				else:
					todo_update['next_status']='REPORT'
	
				todo_update['status']='FREE_USER'
				todo_update['comment']=db_todo['comment'].encode('utf-8')
	

			# 退出内层while 1
			break

		# 更新comment信息
		if todo_update.has_key('comment') and todo_update['comment']!='':
			print '%s: %s' % (todo_update['status'], todo_update['comment'])
		else:
			todo_update['comment']=''

		# 添加 history
		if db_todo.has_key('history'):
			todo_update['history']=db_todo['history']
		else:
			todo_update['history']=[]
		todo_update['history'].append((tname, process_time, db_todo['status'], todo_update['comment']))

		# 更新todo状态
		todo_update['cookie'] = httphelper3.get_cookie(str(db_todo['_id'])) # 保存cookie
		todo_update['e_time'] = int(time.time()) + DELAY  # DELAY 秒后再继续执行
		
		if todo_update['status'] in ('FINISH') or todo_update['man']!=0: 
			#退出while前释放锁
			todo_update['lock'] = 0
			
			# 记录处理事件， 20150404
			todo_update['history'].append((tname, process_time, '%s - break' % todo_update['status']))
		else:
			time.sleep(DELAY)
			print "DELAY %d seconds" % DELAY

		# 更新todo的db数据
		db.todo.update({'_id':db_todo['_id']}, {'$set': todo_update})

		#原则上只有man=1 和 FINISH退出while 1
		if todo_update['status'] in ('FINISH', 'RESERVE_WAIT', 'AUTO_PAY', 'SLEEP', 'SJRAND3_RESULT') or todo_update['man']!=0:
			break

	#print "%s: %s - leave loop $$$$" % (tname, helper.time_str())


class MainLoop(threading.Thread):
	def __init__(self, tid):
		threading.Thread.__init__(self)
		self._tid = tid
		self._tname = None

	def run(self):
		global count, mutex
		self._tname = threading.currentThread().getName()
		
		print 'Thread - %s started.' % self._tname 

		while 1:
			main_loop(self._tname)

			# 周期性打印日志
			#time.sleep(0.2)
			sys.stdout.flush()


if __name__=='__main__':
	print "PROCESSOR: %s started" % helper.time_str()

	gc.set_threshold(300,5,5)

	#线程池
	threads = []
	
	#清理上次遗留的 lock, 分布式部署时，启动时要小心，一定要再没有lock的情况下同时启动分布时进程！！！ 20150403
	db.todo.update_many({'lock':1}, {'$set': {'lock':0}})
	
	# 创建线程对象
	for x in xrange(0, setting.thread_num):
		threads.append(MainLoop(x))
	
	# 启动线程
	for t in threads:
		t.start()

	# 等待子线程结束
	for t in threads:
		t.join()  

	print "PROCESSOR: %s exited" % helper.time_str()
