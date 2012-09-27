# ----------------------------------------------------------------------------------
#								Autoflat.py v1.0
#
#				  An automated flat fielding script for the WFC 
#
#								by James McCormac
# ----------------------------------------------------------------------------------
#
# USAGE: py3.2 Autoflat.py num rspeed f1, f2,..., fn
#

# ----------------------------------------------------------------------------------
# 								Update History
# ----------------------------------------------------------------------------------
# 10/04/12 - 	code writen v1.0
# xx/yy/zz - 	TO BE TESTED
#
#
#

#############################################
#				Modules						#
#############################################

import time, sys, os, os.path
from datetime import date, timedelta
import pyfits as pf
import numpy as np
import commands as cmd

#############################################
#				Variables					#
#############################################

filt_sleep = 15.0
bias_slow = 1000.0
bias_fast = 1200.0 
max_counts = 35000.0
target_counts = 30000.0
min_counts = 20000.0
max_exp = 90.0
min_exp = 2.0
am_tweak = 1.0
pm_tweak = 1.0


#############################################
#				Functions					#
#############################################

def GetAMorPM():
	h_now = int(time.ctime().split()[3].split(':')[0])

	if h_now >= 12:
		print("Afternoon Flats...\n")
		token=0
	if h_now < 12:
		print("Morning Flats...\n")
		token=1
	
	return token


def GetDataDir(token):

	d=date.today()-timedelta(days=token)
	
	x="%d%02d%02d" % (d.year,d.month,d.day)
	
	if os.path.exists("/obsdata/inta/%s" % (x)) == True:
		data_loc="/obsdata/inta/%s" % (x)
	elif os.path.exists("/obsdata/intb/%s" % (x)) == True:
		data_loc="/obsdata/intab/%s" % (x)
	else data_loc = 0

	return data_loc	


def GetFilters():
	n_filt=len(sys.argv) - 3
	
	if n_filt >= 1:	
		filt_list=sys.argv[3:]
		print("Filter(s) %s" % filt_list)

	return n_filt, filt_list


def PrioritiseFilters():
	# Needs setting up for each filter set
	
	return 0


def ChangeFilter(name):
	
	print("Changing filter to %s..." % (name))
	
	os.system('filter %s' % (name))
	time.sleep(filt_sleep)
	
	return 0


def FTest(token,data_loc):
	
	if token == 0:
		test_time=min_exp
	if token == 1:
		test_time=max_exp
	
	os.system('glance %d' % (test_time))
	
	# code to get counts from FTest image
	h=pf.open("%s/s1.fit" % (data_loc))
	data=h[4].data
	
	sky_lvl=np.median(np.median(data, axis=0))-bias_fast
		
	req_exp=test_time/(sky_lvl/target_counts)
	
	return sky_lvl, req_exp


def Flat(token,time,data_loc):

	os.system('flat %.2f' % (time))

	q=os.listdir(data_loc)
	q.sort()
	
	for i in range(0,len(q)):
		if q[i][0] != 'r' or q[i][-4:] != '.fit':
			# dump the value so its not printed out
			dump=q.pop(i)
			
	# choose the last image
	t=q[-1]

	print("Last Image: %s" % t)
	
	h=pf.open("%s/%s" % (data_loc,t))
	data=h[4].data
	
	if sys.argv[3] == "fast":
		bias_lvl=bias_fast
	if sys.argv[3] == "slow":
		bias_lvl=bias_slow
	
	sky_lvl=np.median(np.median(data, axis=0))-bias_lvl
	
	# tweak the required exptime to stop rising and
	# falling counts during calibration phase
	if token == 0:
		tweak=pm_tweak
	if token == 1:
		tweak=am_tweak
	
	req_exp=(time/(sky_lvl/target_counts))*tweak 

	return sky_lvl, req_exp, t


def Offset(j):
	
	shift=j*5	
	os.system('offset arc %d %d' % (shift, shift))

	return 0


#############################################
#					Main					#
#############################################

if len(sys.argv) < 4:
	print("USAGE: py3.2 Autoflat.py num rspeed f1, f2,..., fn\n")
	sys.exit()

# check current time for morning 
# or afternoon
token=GetAMorPM()

# Get tonights directory
data_loc=GetDataDir(token)
if data_loc == 0:
	print("Error finding data folder, exiting!\n")
	sys.exit()

# Get the number and list of filters 
n_filt,filt_list=GetFilters()

# Prioritise Filters
#if n_filt > 1:
	# Needs Calibrating 
	# Setup Filter Sequence 
	# filt_seq=[]

if n_filt == 1:
	filt_seq=filt_list

# start looping over the filters
for i in range(0,len(filt_seq)):
	
	j=0
	
	# change filter
	c1=ChangeFilter(filt_seq[i])
	if c1 != 0:
		print("Problem Changing Filter, exiting!\n")
		sys.exit()
	
	# dusk flats
	if token==0:
		
		# set a window + fast readout for quick sky level checks
		os.system('window 1 "[900:1100,1900:2100]"')
		os.system('rspeed fast')
		
		# take an FTest image to check sky level
		sky_lvl,req_exp=FTest(token,data_loc) 
		
		# if the required exp time is less than minimum
		# loop checking the sky until it is in range
		while req_exp < min_exp:
			sky_lvl,req_exp=FTest(token,data_loc)
			print("[Sky level]: %d counts - [Required ExpTime]: %.2f - Waiting..." % (sky_lvl, req_exp))
			time.sleep(10)
		
		# when in range set the rspeed to that on command line
		# disable the FTest window
		if req_exp >= min_exp and req_exp <= max_exp and sky_lvl >= min_counts and sky_lvl <= max_counts:
			print("Sky level within range...")
			print("Setting rspeed to $s..." % (sys.argv[3]))
			os.system('rspeed %s' % (sys.argv[3]))
			print("Disabling window...\n")
			os.system('window 1 disable')
			
			# loop over the requested number of flats per filter
			while j < sys.argv[2]:
				# take a flat at the last required exp time
				sky_lvl,req_exp,t=Flat(token,req_exp,data_loc)
				
				# if the median counts are within range accept the flat
				# increase counters and offset the telescope for the next flat
				if sky_lvl > min_counts and sky_lvl < max_counts:
					j=j+1	
					print("[%d/%d] Flat %s successful..." % (j,sys.argv[2],t))
					o1=Offset(j)
					if o1 != 0:
						print("Problem offseting, exiting!\n")
						sys.exit() 
				
				# if the new exp time if good continue
				if req_exp >= min_exp and req_exp <= max_exp:
					continue
				# if not exit while loop
				if req_exp < min_exp or req_exp > max_exp:
					break
					
			# reset telescope pointing to 0 0 for next filter	
			o1=Offset(0)		
	
	# dawn flats
	if token==1:
		
		# set a window + fast readout for quick sky level checks
		os.system('window 1 "[900:1100,1900:2100]"')
		os.system('rspeed fast')
		
		# take an FTest image to check sky level
		sky_lvl,req_exp=FTest(token,data_loc) 
		
		# if the required exp time is less than minimum
		# loop checking the sky until it is in range
		while req_exp > max_exp:
			sky_lvl,req_exp=FTest(token,data_loc)
			print("[Sky level]: %d counts - [Required ExpTime]: %.2f - Waiting..." % (sky_lvl, req_exp))
			time.sleep(5)
		
		# when in range set the rspeed to that on command line
		# disable the FTest window
		if req_exp > min_exp and req_exp < max_exp and sky_lvl > min_counts and sky_lvl < max_counts:
			print("Sky level within range...")
			print("Setting readout speed...")
			os.system('rspeed %s' % (sys.argv[3]))
			print("Disabling window...\n")
			os.system('window 1 disable')
			
			# loop over the requested number of flats per filter
			while j < sys.argv[2]:
				# take a flat at the last required exp time
				sky_lvl,req_exp,t=Flat(token,req_exp,data_loc)
				
				# if the median counts are within range accept the flat
				# increase counters and offset the telescope for the next flat
				if sky_lvl > min_counts and sky_lvl < max_counts:
					j=j+1	
					print("Flat %s %d/%d successful..." % (t,j,sys.argv[2]))
					o1=Offset(j)
					if o1 != 0:
						print("Problem offseting, exiting!\n")
						sys.exit() 
				
				# if the new exp time if good continue
				if req_exp >= min_exp and req_exp <= max_exp:
					continue
				# if not exit while loop
				if req_exp < min_exp or req_exp > max_exp:
					break
					
			# reset telescope pointing to 0 for next filter	
			o1=Offset(0)
		
		
