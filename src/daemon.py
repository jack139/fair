#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 后台daemon进程，启动后台处理进程，并检查进程监控状态
#

import sys
import time, shutil, os
import helper
from config import setting

db = setting.db_web

FAIR_DIR=''
LOG_DIR=''

def start_processor(pname):
	cmd0="nohup python %s/%s.pyc &>> %s/%s.log &" % \
		(FAIR_DIR, pname, LOG_DIR, pname)
	#print cmd0
	os.system(cmd0)

def get_processor_pid(pname):
	cmd0='pgrep -f "%s"' % pname
	#print cmd0
	pid=os.popen(cmd0).readlines()
	if len(pid)>0:
		return pid[0].strip()
	else:
		return None

def kill_processor(pname):
	cmd0='kill -9 `pgrep -f "%s"`' % pname
	#print cmd0
	os.system(cmd0)

if __name__=='__main__':
	if len(sys.argv)<3:
		print "usage: daemon.py <FAIR_DIR> <LOG_DIR>"
		sys.exit(2)

	FAIR_DIR=sys.argv[1]
	LOG_DIR=sys.argv[2]

	print "DAEMON: %s started" % helper.time_str()
	print "FAIR_DIR=%s\nLOG_DIR=%s" % (FAIR_DIR, LOG_DIR)

	#
	#启动后台进程
	#
	kill_processor('%s/elm_dispatcher' % FAIR_DIR)
	start_processor('elm_dispatcher')

	try:	
		_count=_ins=0
		while 1:						
			# 检查processor进程
			pid=get_processor_pid('%s/elm_dispatcher' % FAIR_DIR)
			if pid==None:
				# 进程已死, 重启进程
				kill_processor('%s/elm_dispatcher' % FAIR_DIR)
				start_processor('elm_dispatcher')
				_ins+=1
				print "%s\telm_dispatcher restart" % helper.time_str()
						
			time.sleep(5)
			if _count>1000:
				if _ins>0:
					print "%s  HEARTBEAT: error %d" % (helper.time_str(), _ins)
				else:
					print "%s  HEARTBEAT: fine." % (helper.time_str())
				_count=_ins=0
			sys.stdout.flush()

	except KeyboardInterrupt:
		print
		print 'Ctrl-C!'

	print "DAEMON: %s exited" % helper.time_str()
