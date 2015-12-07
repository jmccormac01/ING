
#########################################################
#                                                       #
#                    autoflat v1.2                   	#
#                                                       #
#          James McCormac & Patrick Sandquist           #
#                                                       #
#########################################################
#
#   Revision History:	
#   v1.0   27/06/13  -  Original script editted to include a camera command - JMCC
#   v1.2   15/07/13  -  Script tested at the telescope several bugs corrected - JMCC
#
#   To do:
#       Complete the camera commands to include more than ACAM
#	Eliminate sleep calls? (bias remains)
#	Make sure the 4 windows are not overlapping (will cause CCD error)
#	Find and update the correct names of the filters in the filter database

import sys

# check command line args
# make more detailed when FilterDB is full
if len(sys.argv) < 5:
	print("USAGE: pyver autoflat.py camera num_flats_per_filt rspeed f1 f2 ... fn\n")
	sys.exit(1)

from datetime import date, timedelta
import os, os.path, time
import pyfits as pf
import numpy as np
import signal

print("Modules loaded...")

# Global Varibales #

#filt_sleep = 10.0
max_counts = 35000.0
target_counts = 30000.0
min_counts = 15000.0
max_exp = 120.0
min_exp = 0.5
am_tweak = 1.00
pm_tweak = 1.00
fast_slow_gain=2.02
camera_name=sys.argv[1]
chip=1

# WFC
# fast_slow_gain = 1.95
# min_exp = 2.0
# am_tweak = 0.70
# pm_tweak = 1.25

f_db='/home/whtobs/acam/jmcc/under_development/autoflat/FilterDB.txt'
bias_db='/home/whtobs/acam/jmcc/under_development/autoflat/BiasLevelDB.txt'


# Functions #
# add save/setccd functionality

# Returns zero when the camera is idle
def WaitForIdle():
	idle=""
	while idle != "idling":
		if camera_name == 'acam':
			idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]
		#if camera_name == 'pfip':
			# add more...

		time.sleep(1)
		if idle == "idling":
			return 0


# Returns zero when the telescope is tracking
def WaitForTracking():
	stat=""
	while stat != "TRACKING":
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		time.sleep(1)
		if stat == "TRACKING":
			return 0


# Returns zero when the filter wheel is ready (only works for one filter being in place!)
def WaitForFilterWheels(required_filter_serial_num):
	
	# needs string for comparing to those below
	required_filter_serial_num=str(required_filter_serial_num)
	
	while (1):
		wheel1_serial_num = os.popen('ParameterNoticeBoardLister -i CAGB.WHB.SERIALNUMBER').readline().split('\n')[0]
		wheel2_serial_num = os.popen('ParameterNoticeBoardLister -i CAGB.WHA.SERIALNUMBER').readline().split('\n')[0]
		wheel1_opticalelementtype = os.popen('ParameterNoticeBoardLister -i CAGB.WHB.OPTICALELEMENTTYPE').readline().split('\n')[0]
		wheel2_opticalelementtype = os.popen('ParameterNoticeBoardLister -i CAGB.WHA.OPTICALELEMENTTYPE').readline().split('\n')[0]
				
		if wheel2_serial_num == required_filter_serial_num and wheel1_opticalelementtype == "UNKNOWN" or wheel1_serial_num == required_filter_serial_num and wheel2_opticalelementtype == "UNKNOWN":
				
			return 0
		else:
			return 1
			#time.sleep(1)


def GetAMorPM():

	h_now=int(time.ctime().split()[3].split(':')[0])	# finds the current hour

	if h_now >= 12:
		print("Afternoon Flats...")
		token=0		# token is zero for the afternoon
	if h_now < 12:
		print("Morning Flats...")
		token=1		# token is 1 for the morning

	return token


def GetDataDir(token):
	d=date.today()-timedelta(days=token)	# time of last data recorded?
	
	x="%d%02d%02d" % (d.year,d.month,d.day)
	
	if os.path.exists("/obsdata/whta/%s" % (x)) == True:	# looks for the data directory
		data_loc="/obsdata/whta/%s" % (x)
	elif os.path.exists("/obsdata/whtb/%s" % (x)) == True:
		data_loc="/obsdata/whtb/%s" % (x)
	else: 
		data_loc =0
	
	return data_loc
	
	
def GetFilters():

	n_filt=len(sys.argv) - 4	# the number of filters
	
	if n_filt >= 1:				# if there are filters being used,
		filt_list=sys.argv[4:]	# fill filt_list with the names given in the argv (from 3 to the end)
		print("Filter(s): %s" % filt_list)
	
	return n_filt, filt_list


def SortFilters(token,f_list):

	f=open(f_db,'r').readlines()	# open the filter database and read all the lines into f

	name,BoN,cen_wave,width,num,mimic=[],[],[],[],[],[]	# create lists for the variables

	for i in range(0,len(f)):	# for each of the filters in the database,
		name.append(f[i].split()[0])	# add the filter names to the name list
		cen_wave.append(f[i].split()[1])# add the center wavelength to the correct list
		width.append(f[i].split()[2])	# beam width
		BoN.append(f[i].split()[-1]) 	# broad or narrow character
		num.append(f[i].split()[3])	# the filter number
		mimic.append(f[i].split()[4])	# the filter discription

	id_n,cwl_n,wl_n,id_b,cwl_b,wl_b,num_b,num_n=[],[],[],[],[],[],[],[]
	
	# create 2 lists for narrow and broad band filters
	for i in range(0,len(f_list)):	# for each of the filters that the user wants to use,
		for j in range(0,len(f)):	# for each of the filters in the database,
			if f_list[i] == name[j]:	# if the desired filter is in the database,
				if BoN[j] == 'B':		# add the properties to the correct list
					id_b.append(name[j])
					cwl_b.append(cen_wave[j])
					wl_b.append(width[j])
					num_b.append(num[j])
				if BoN[j] == 'N':
					id_n.append(name[j])
					cwl_n.append(cen_wave[j])
					wl_n.append(width[j])
					num_n.append(num[j])
		
		if f_list[i] not in name:
			print("Filter not found: %s" % (f_list[i]))
			
	# sort the two lists
	if len(cwl_b) > 0:	# if there are filters in the broad lists,	
		x=list(zip(cwl_b,wl_b,id_b,num_b))	# make list x which contains all of the information (filter properties are grouped together)
		x.sort()	# sort the list (will be sorted by central wavelength (blue to red) while maintaining the filter grouping)
		cwl_b,wl_b,id_b,num_b=zip(*x)	# unzips the list sorted by central wavelength

	if len(cwl_n) > 0:
		y=list(zip(cwl_n,wl_n,id_n,num_n))
		y.sort()
		cwl_n,wl_n,id_n,num_n=zip(*y)
	
	# test using filters in reverse order
	# afternoon	
	if token == 0:
		flat_list=list(id_n)+list(id_b)	# make flats list by narrows then broads (id_n and id_b are sorted from blue to red)
		serial_list=list(num_n)+list(num_b)	# make serial number list arranged n to b sorted by wavelength
		print("Afternoon filter order:")
		print(flat_list)

	# morning
	if token == 1:
		flat_list=list(id_b)[::-1]+list(id_n)[::-1]	# flats list arranged broad then narrow (both red to blue)
		serial_list=list(num_b)[::-1]+list(num_n)[::-1]	# serial number list arranged b to n by wavelength
		print("Morning filter order:")
		print(flat_list)
	
	return (flat_list, serial_list)


def ChangeFilter(name, serial_number):
	
	print("Changing filter to %s..." % (name))
	
	if camera_name == 'acam':
		os.system('acamimage %s' % name)
	#if camera_name == 'pfip':
		# add more

	# check to see if the filter wheel is ready
	ready = WaitForFilterWheels(serial_number)
	if ready != 0:
		print "Unexpected response while waiting for the filter wheels, aborting!"
		os.system('abort %s &' % camera_name)

	return 0	


def GetLastImage(data_loc):
	
	q=os.listdir(data_loc)	# a list of the names of the entries in data_loc directory
	q.sort()	# sort the list (alpha numeric)
	
	im_list=[]
	for i in range(0,len(q)):	# for each entry in the directory,
		if q[i][0] == 'r' and q[i][-4:] == '.fit':	# if the first character in the string is 'r' and the last 4 are '.fit',
			im_list.append(q[i])	# add the filename to the new list
	
	# choose the last image (the most recent)
	t=im_list[-1]
	
	return t


# add to save bias to file and check there first for the current day
def GetBiasLevel(data_loc):
	
	print("Getting fast and slow bias levels")
	
	# BiasLevelDB.txt e.g. format:
	# 6 Mar 2013 bias_s bias_f
	
	# check the BiasLevelDB.txt file for bias levels first
	lday,lmonth,lyear,lbias_s,lbias_f=open(bias_db).readlines()[-1].split()[:5]	# from the last line of the bias file, split the line and add to the appropriate lists
	
	# get date now
	now=time.ctime()
	day = now.split()[2]
	month = now.split()[1]
	year = now.split()[-1]
	
	# compare to last date from log, if different work out the bias level again
	# if the day is the same just use what is in the database
	if lday == day and lmonth == month and lyear == year:	# if the day is the same,
		print('Bias levels in database, using these values...')
		bias_s = float(lbias_s)	# use the information from the database (float converts from string to float)
		bias_f = float(lbias_f)
	
	if lday != day or lmonth != month or lyear != year:	# if there is no bias level in the database,
		
		print('No bias levels in database, taking bias images to check...')
		
		# fast 
		os.system('rspeed %s fast' % camera_name)
		os.system('bias %s' % camera_name)
	
		time.sleep(1)
		
		t=GetLastImage(data_loc)
		
		h=pf.open('%s/%s' % (data_loc,t))
		data=h[1].data
		
		bias_f=np.median(np.median(data, axis=0))	# finds the median value of rows and then columns
		
		# slow
		os.system('rspeed %s slow' % camera_name)
		os.system('bias %s' % camera_name)

		time.sleep(1)
		
		t2=GetLastImage(data_loc)
		
		h2=pf.open('%s/%s' % (data_loc,t2))
		data2=h2[1].data
		
		bias_s=np.median(np.median(data2, axis=0))
		
		print("Bias Slow: %.2f ADU" % (bias_s))
		print("Bias Fast: %.2f ADU" % (bias_f))
		
		# save the bias levels to the BiasLevelDB.txt
		f=open(bias_db,'a')
		f.write("%s  %s  %s  %s  %s\n" % (day,month,year,bias_s,bias_f))
		f.close()
		
		# set rspeed to fast again for FTest
		os.system('rspeed %s fast' % camera_name)
	
	return bias_f, bias_s


# take a test image of the centre of the CCD to save time
def FTest(token,data_loc,bias_f):
	
	if token == 0:	# afternoon
		test_time = 2
	if token == 1:	# morning
		test_time = 10	
	
	# test when at testscope
	os.system('glance %s %d' % (camera_name,test_time)) 

	idle=WaitForIdle() # check to see if the camera is idle
	if idle != 0:
		print "Unexpected response while waiting for CCD to idle, aborting!"
		os.system('abort %s &' % camera_name)

		exit()
	
	# code to get median counts from test image
	h=pf.open('%s/s1.fit' % (data_loc))
	data=h[1].data
	
	sky_lvl=np.median(np.median(data, axis=0))-bias_f	# take the median of the image and subtract the bias level (a median) to obtain the sky level
		
	if token == 0:	# afternoon
		req_exp=test_time/(sky_lvl/target_counts)
		
		# account for gain difference between fast and slow rspeeds
		if sys.argv[3] == 'slow':
			req_exp=req_exp/fast_slow_gain
		
		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))

	if token == 1:	# morning
		if sky_lvl <= 64000:
			req_exp=test_time/(sky_lvl/target_counts)
			
			# account for gain difference between fast and slow rspeeds
			if sys.argv[3]=='slow':
				req_exp=req_exp/fast_slow_gain
		
		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))
			
		if sky_lvl > 64000:
			req_exp=test_time*0.1
			if req_exp<min_exp:
				# no need to account for difference in gains as using the lowest exp time
				# and cannot go lower
				req_exp=min_exp
				print ("[Ftest] Sky level saturating, trying %.2f sec" % (req_exp))
		
	return sky_lvl, req_exp
	

# take the flat image
def Flat(token,flat_time,data_loc,bias):
	# tell system to take a flat
	os.system('flat %s %.2f' % (camera_name,flat_time))
	
	idle=WaitForIdle() # check that the camera is idle
	if idle != 0:
		print "Unexpected response while waiting for CCD to idle, aborting!"
		os.system('abort %s &' % camera_name)

		exit()

	t=GetLastImage(data_loc)
	
	h=pf.open('%s/%s' % (data_loc, t))[chip].data
	
	# check counts in centre of image
	y=h.shape[0]/2.0
	x=h.shape[1]/2.0
	
	data=h[y-100:y+100,x-100:x+100]	# data is the 200x200 box centred at the origin
	
	sky_lvl=np.median(np.median(data, axis=0))-bias		# subtract the bias
	
	# tweak the required exptime to stop rising and
	# falling counts during calibration phase to account for change between when image is taken and read off
	if token == 0:
		tweak=pm_tweak
	if token == 1:
		tweak=am_tweak

	if sky_lvl <= 64000:
		req_exp=(flat_time/(sky_lvl/target_counts))*tweak
		print("[Flat: %s] Sky Level: %d Required Exptime: %.2f" % (t,int(sky_lvl),req_exp))

	if sky_lvl > 64000:
		req_exp=flat_time*0.1
		if req_exp<min_exp:
			req_exp=min_exp
		print ("[Flat: %s] Sky level saturating, trying %.2f sec" % (t,req_exp))
		
	
	return sky_lvl,req_exp,t


def Offset(j):

	shift=j*5
	print("Offset to %d %d..." % (shift, shift))
	os.system('offset arc %d %d' % (shift, shift))
	
	done=WaitForTracking()
	if done != 0:
		print "Unexpected response while waiting for telescope to resume tracking, aborting!"
		os.system('abort %s &' % camera_name)

		exit()
	
	return 0

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print('   Ctrl+C caught, shutting down...')
	os.system('abort %s &' % camera_name)

	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


######################################
################ Main ################
######################################

DEBUG = 0

if DEBUG == 0:
	# get afternoon or morning			
	#token = GetAMorPM()
	token = 0
	
	# get tonights folder
	data_loc=GetDataDir(token)
	if data_loc==0:
		print("Error finding data folder, exiting!")
		sys.exit()
		
	# get the list of filters	
	n_filt,filt_list=GetFilters()
	
	# sort the filters
	filt_seq, serial_seq = SortFilters(token,filt_list)
	
	# begin looping over required number of flats	
	for i in range(0,len(filt_seq)):	# for each filter,
		
		j = 0	# what number flat we are on
	
		# change to new filter
		c1=ChangeFilter(filt_seq[i], serial_seq[i])
		if c1 != 0:
			print("Problem changing filter, exiting!\n")
			sys.exit()
		
		# afternoon
		if token == 0:
			
			# set a window and fast readout speed
			print("Setting up FTest window and rspeed to fast...")
			if camera_name == 'acam':
				os.system('window acam 1 "[875:1850,1275:2250]"')
				os.system('rspeed acam fast')
			#if camera_name == 'pfip':
				# add more
		
	
			# get the bias level in real time to account for any slight changes
			if i == 0:	# do for first flat only
				bias_f,bias_s=GetBiasLevel(data_loc)
			
			# take an FTest image to check the sky level
			print("Checking sky level...")
			sky_lvl,req_exp=FTest(token,data_loc,bias_f)
		
			if req_exp > max_exp:
				print ("It's too dark for this filter, next!")
				if filt_seq[i] == filt_seq[-1]:	# if on the last filter,
					print ("No filters left, quiting!")
					print("Disabling FTest window...")
					os.system('window %s 1 disable' % camera_name)
					print("Setting rspeed back to %s..." % (sys.argv[3]))
					os.system('rspeed %s %s' % (camera_name,sys.argv[3]))
		
					break	# leave the for loop
	
			# if the required exp time is less than the minimum (sky too bright)
			# loop checking the sky until it is in range
			while req_exp < min_exp:
				sky_lvl,req_exp=FTest(token,data_loc,bias_f)
				print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
				time.sleep(15)
			
			# when in range set the rspeed to that on commandline
			# disable the FTest window
			if req_exp >= min_exp and req_exp <= max_exp:
				print("Exposure time within range...")
				print("Setting rspeed back to %s..." % (sys.argv[3]))
				if camera_name == 'acam':
					os.system('rspeed acam %s' % (sys.argv[3]))
					print("Disabling FTest window...")
					os.system('window acam 1 disable')
				#if camera_name == 'pfip':
					# add more
				
				
				while j < int(sys.argv[2]):	# while there are more flats to take,
					# take a flat at the last required exptime
					if sys.argv[3]=="fast":
						sky_lvl,req_exp,t = Flat(token,req_exp,data_loc,bias_f)
					if sys.argv[3]=="slow":
						sky_lvl,req_exp,t = Flat(token,req_exp,data_loc,bias_s)
					
					if req_exp > max_exp:
						print ("It's too dark, quiting!")
						break
	
					# if the median count are within range accept the flat
					# increase the counter and offset telescope for next flat
					if sky_lvl > min_counts and sky_lvl < max_counts:
						j=j+1
						print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[2]),t))
						
						# dont offset for the final image of a filter
						if j < int(sys.argv[2]):
							o1=Offset(j)
							if o1 != 0:
								print("Problem offsetting, exiting!\n")
								sys.exit()
							
					if req_exp <= max_exp:
						continue
				
				# reset telescope pointing to 0 0 for next filter
				o1=Offset(0)
		
		# morning
		if token == 1:
			
			# set a window and fast readout speed
			print("Setting up FTest window and rspeed to fast...")
			if camera_name == 'acam':
				os.system('window acam 1 "[875:1850,1275:2250]"')
				os.system('rspeed acam fast')
			#if camera_name == 'pfip':
				# add more
		
			# get the bias level in real time to acount for any slight changes
			# do for first flat only	
			if i == 0:
				bias_f,bias_s=GetBiasLevel(data_loc)
			
			# take an FTest image to check the sky level
			print("Checking sky level...")
			sky_lvl,req_exp=FTest(token,data_loc,bias_f)
	
			# sky_lvl > 64000 and <-- removed to solve <2s issue at end of morning flats
			if req_exp < min_exp:
				print ("It's too bright for this filter, next!")
				if filt_seq[i] == filt_seq[-1]:
					print ("No filters left, quiting!")
					print("Disabling FTest window...")
					if camera_name == 'acam':
						os.system('window acam 1 disable')
						print("Setting rspeed back to %s..." % (sys.argv[3]))
						os.system('rspeed acam %s' % (sys.argv[3]))
					#if camera_name == 'pfip':
						# add more
					
					break
	
	
			# if the required exp time is less than the minimum
			# loop checking the sky until it is in range
			while req_exp > max_exp:	# sky is too dark
				sky_lvl,req_exp=FTest(token,data_loc,bias_f)
				print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
				time.sleep(15)
			
			# when in range set the rspeed to that on commandline
			# disable the FTest window
			if req_exp >= min_exp and req_exp <= max_exp:
				print("Exposure time within range...")
				print("Setting rspeed back to %s..." % (sys.argv[3]))
				if camera_name == 'acam':
					os.system('rspeed acam %s' % (sys.argv[3]))
					print("Disabling FTest window...")
					os.system('window acam 1 disable')
				#if camera_name == 'pfip':
					# add more
		
				while j < int(sys.argv[2]):
					# take a flat at the last required exptime
					if sys.argv[3]=="fast":
						sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_f)
					if sys.argv[3]=="slow":
						sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_s)
					
					if req_exp < min_exp:
						print ("It's too bright, quiting!")
						break
					
					# if the median count are within range accept the flat
					# increase the counter and offset telescope for next flat
					if sky_lvl > min_counts and sky_lvl < max_counts:
						j=j+1	# go to next flat
						print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[2]),t))
						
						# don't offset for the final image of a filter
						if j < int(sys.argv[2]):
							o1=Offset(j)
							if o1 != 0:
								print("Problem offsetting, exiting!\n")
								sys.exit()
							
					if req_exp >= min_exp:
						continue
				
				# reset telescope pointing to 0 0 for next filter
				o1=Offset(0)
					
					
