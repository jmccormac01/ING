# ----------------------------------------------------------------------------------
#								acam_alt.py v1.0
#
#				 	 An script for observing in alternate filters
#
#								by James McCormac
# ----------------------------------------------------------------------------------
#
# USAGE: python acam_alt.py time1 time2 f1, f2,..., fn
#

# ----------------------------------------------------------------------------------
# 								Update History
# ----------------------------------------------------------------------------------
# 14/04/12 - 	code writen v1.0
# 14/04/12 - 	TO BE TESTED
#
#


#############################################
#				Modules						#
#############################################

import os, time, sys
from datetime import datetime

#############################################
#				Variables					#
#############################################

# target time for stopping
h_tar=3
m_tar=33

# image counters
x=0
im_count=1

#############################################
#					Main					#
#############################################

# get filter list
filt_list=sys.argv[3:]
time_list=sys.argv[1:3]

while x < 1:
	h_now=datetime.now().hour
	m_now=datetime.now().minute

	if h_now >= h_tar and m_now >= m_tar:
		x=1
	else: x=0

	for i in range(0,len(filt_list)):
		print "Changing filter to %s..." % (filt_list[i])
		os.system("acamimage %s" % (filt_list[i]))
		time.sleep(10)
		print "Imaging %s %d" % (filt_list[i],im_count)
		os.system("glance acam %s" % (time_list[i]))
		time.sleep(3)
		
	im_count=im_count+1
	
	