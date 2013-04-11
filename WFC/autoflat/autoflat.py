
#########################################################
#                                                       #
#                  autoflat WFC v1.4                    #
#                     *not tested*                      #
#                    James McCormac                     #
#                                                       #
#########################################################
#
#   Revision History:	
#   v1.1   13/08/12 - fixed <2s bug for morning flats
#   v1.2   27/09/12 - fixed FTest bug by removing tweak
#                   - added GetLastImage() and GetBiasLevel() 
#   v1.3   04/10/12 - added	 CTRL+C trapping, moved FTest boxed as 
#                     was measuring dark region at centre of CCD
#                     made GetBiasLevel() for first flat only
#                     added Filter sorting, tested.
#                     fixed last filt not removing FTest conditions if
#                     too dark or bright to continue
#                     fixed gain difference between fast and slow rspeeds, 
#                     this was real cause of FTest predicting twice req_exp
#   v1.4   06/03/13 - added usage before loading the modules
#                     added a BiasLevelDB.txt file to save bias levels so 
#                     they dont need worked out each time the script is run
#          03/04/13 - trying the reverse filter order as suggested by ovidiu
#                     to see if we get more flats.
#                     fixed bug where autoflat quitted if one filter was out
#                     of range. Now tries next filters until the end of the list
#          11/04/13 - reversing filter order was inconclusive, replacing normal
#                     order. U has been added to narrow band filters in DB as
#                     the throughput is so bad
#
#   To do:
#       Add windowed flats capability
#       Add binning capability


import sys

# check command line args
# make more detailed when FilterDB is full
if len(sys.argv) < 4:
	print("USAGE: pyver autoflat.py num_flats_per_filt rspeed f1 f2 ... fn\n")
	sys.exit(1)

from datetime import date, timedelta
import os, os.path, time
import pyfits as pf
import numpy as np
import signal

print("Modules loaded...")

# Global Varibales #

filt_sleep = 10.0
offset_sleep = 5.0
max_counts = 35000.0
target_counts = 30000.0
min_counts = 20000.0
max_exp = 200.0
min_exp = 2.0
am_tweak = 0.75
pm_tweak = 1.25
fast_slow_gain=1.95

f_db='/home/intobs/jmcc/FilterDB.txt'
bias_db='/home/intobs/jmcc/BiasLevelDB.txt'


# Functions #

def GetAMorPM():

	h_now=int(time.ctime().split()[3].split(':')[0])	

	if h_now >= 12:
		print("Afternoon Flats...")
		token=0
	if h_now < 12:
		print("Morning Flats...")
		token=1

	return token


def GetDataDir(token):
	d=date.today()-timedelta(days=token)
	
	x="%d%02d%02d" % (d.year,d.month,d.day)
	
	if os.path.exists("/obsdata/inta/%s" % (x)) == True:
		data_loc="/obsdata/inta/%s" % (x)
	elif os.path.exists("/obsdata/intb/%s" % (x)) == True:
		data_loc="/obsdata/intb/%s" % (x)
	else: 
		data_loc =0
	
	return data_loc
	
	
def GetFilters():

	n_filt=len(sys.argv) - 3
	
	if n_filt >= 1:
		filt_list=sys.argv[3:]
		print("Filter(s): %s" % filt_list)
	
	return n_filt, filt_list


def SortFilters(token,f_list):

	f=open(f_db,'r').readlines()

	name,BoN,cen_wave,width,num,mimic=[],[],[],[],[],[]

	for i in range(0,len(f)):
		name.append(f[i].split()[0])
		cen_wave.append(f[i].split()[1])
		width.append(f[i].split()[2])
		BoN.append(f[i].split()[3]) 
		num.append(f[i].split()[4])
		mimic.append(f[i].split()[5])

	id_n,cwl_n,wl_n,id_b,cwl_b,wl_b=[],[],[],[],[],[]
	
	# create 2 lists for narrow and broad band filters
	for i in range(0,len(f_list)):
		for j in range(0,len(f)):
			if f_list[i] == mimic[j]:
				if BoN[j] == 'B':
					id_b.append(mimic[j])
					cwl_b.append(cen_wave[j])
					wl_b.append(width[j])
				if BoN[j] == 'N':
					id_n.append(mimic[j])
					cwl_n.append(cen_wave[j])
					wl_n.append(width[j])
		
		if f_list[i] not in mimic:
			print("Filter not found: %s" % (f_list[i]))
			
	# sort the two lists
	if len(cwl_b) > 0:	
		x=list(zip(cwl_b,wl_b,id_b))
		x.sort()
		cwl_b,wl_b,id_b=zip(*x)

	if len(cwl_n) > 0:
		y=list(zip(cwl_n,wl_n,id_n))
		y.sort()
		cwl_n,wl_n,id_n=zip(*y)
	
	# test using filters in reverse order
	# afternoon	
	if token == 0:
		flat_list=list(id_n)+list(id_b)
		#flat_list=list(id_n)[::-1]+list(id_b)[::-1]
		print("Afternoon filter order:")
		print(flat_list)

	# morning
	if token == 1:
		flat_list=list(id_b)[::-1]+list(id_n)[::-1]
		#flat_list=list(id_b)+list(id_n)
		print("Morning filter order:")
		print(flat_list)
	
	return flat_list


def ChangeFilter(name):
	
	print("Changing filter to %s..." % (name))
	
	os.system('filter %s' % (name))
	time.sleep(filt_sleep)

	
	return 0	


def GetLastImage(data_loc):
	
	q=os.listdir(data_loc)
	q.sort()
	
	im_list=[]
	for i in range(0,len(q)):
		if q[i][0] == 'r' and q[i][-4:] == '.fit':
			im_list.append(q[i])
	
	# choose the last image
	t=im_list[-1]
	
	return t


# add to save bias to file and check there first for the current day
def GetBiasLevel(data_loc):
	
	print("Getting fast and slow bias levels")
	
	# BiasLevelDB.txt e.g. format:
	# 6 Mar 2013 bias_s bias_f
	
	# check the BiasLevelDB.txt file for bias levels first
	lday,lmonth,lyear,lbias_s,lbias_f=open(bias_db).readlines()[-1].split()[:5]
	
	# get date now
	now=time.ctime()
	day = now.split()[2]
	month = now.split()[1]
	year = now.split()[-1]
	
	# compare to last date from log, if different work out the bias level again
	# if the day is the same just use what is in the database
	if lday == day and lmonth == month and lyear == year:
		print('Bias levels in database, using these values...')
		bias_s = float(lbias_s)
		bias_f = float(lbias_f)
	
	if lday != day or lmonth != month or lyear != year:
		
		print('No bias levels in database, taking bias images to check...')
		
		# fast
		os.system('bias') 
		time.sleep(1)
		
		t=GetLastImage(data_loc)
		
		h=pf.open('%s/%s' % (data_loc,t))
		data=h[1].data
		
		bias_f=np.median(np.median(data, axis=0))
		
		# slow
		os.system('rspeed slow')
		
		os.system('bias')
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
		os.system('rspeed fast')
	
	return bias_f, bias_s


def FTest(token,data_loc,bias_f):
	
	if token == 0:
		test_time = 2
	if token == 1:
		test_time = 10	
	
	# test when at testscope
	os.system('glance %d' % (test_time))
	
	time.sleep(3)
	
	# code to get median counts from test image
	h=pf.open('%s/s1.fit' % (data_loc))
	data=h[1].data
	
	sky_lvl=np.median(np.median(data, axis=0))-bias_f
		
	if token == 0:
		req_exp=test_time/(sky_lvl/target_counts)
		
		# account for gain difference between fast and slow rspeeds
		if sys.argv[2] == 'slow':
			req_exp=req_exp/fast_slow_gain
		
		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))

	if token == 1:
		if sky_lvl <= 64000:
			req_exp=test_time/(sky_lvl/target_counts)
			
			# account for gain difference between fast and slow rspeeds
			if sys.argv[2]=='slow':
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
	

def Flat(token,flat_time,data_loc,bias):
	
	os.system('flat %.2f' % (flat_time))
	
	time.sleep(3)
	
	t=GetLastImage(data_loc)
	
	h=pf.open('%s/%s' % (data_loc, t))[4]
	
	# check counts in centre of image
	y=h.shape[0]/2
	x=h.shape[1]/2
	
	data=h.data[y-100:y+100,x-100:x+100]
		
	sky_lvl=np.median(np.median(data, axis=0))-bias
	
	# tweak the required exptime to stop rising and
	# falling counts during calibration phase
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
	time.sleep(offset_sleep)
	
	return 0

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print('   Ctrl+C caught, shutting down...')
	os.system('abort &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


######################################
################ Main ################
######################################

# get afternoon or morning			
token = GetAMorPM()

# get tonights folder
data_loc=GetDataDir(token)
if data_loc==0:
	print("Error finding data folder, exiting!")
	sys.exit()
	
# get the list of filters	
n_filt,filt_list=GetFilters()

# sort the filters
filt_seq=SortFilters(token,filt_list)

# begin looping over required number of flats	
for i in range(0,len(filt_seq)):
	
	j = 0	

	# change filter
	c1=ChangeFilter(filt_seq[i])
	if c1 != 0:
		print("Problem changing filter, exiting!\n")
		sys.exit()
	
	# afternoon
	if token == 0:
		
		# set a window and fast readout speed
		print("Setting up FTest window and rspeed to fast...")
		os.system('window 1 "[800:1200,2400:2800]"')
		os.system('rspeed fast')

		# get the bias level in real time to acount for any slight changes
		# do for first flat only	
		if i == 0:
			bias_f,bias_s=GetBiasLevel(data_loc)
		
		# take an FTest image to check the sky level
		print("Checking sky level...")
		sky_lvl,req_exp=FTest(token,data_loc,bias_f)
	
		if req_exp > max_exp:
			print ("It's too dark for this filter, next!")
			if filt_seq[i] == filt_seq[-1]:
				print ("No filters left, quiting!")
				print("Disabling FTest window...")
				os.system('window 1 disable')
				print("Setting rspeed back to %s..." % (sys.argv[2]))
				os.system('rspeed %s' % (sys.argv[2]))
				break

		# if the required exp time is less than the minimum
		# loop checking the sky until it is in range
		while req_exp < min_exp:
			sky_lvl,req_exp=FTest(token,data_loc,bias_f)
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
			time.sleep(15)
		
		# when in range set the rspeed to that on commandline
		# disable the FTest window
		if req_exp >= min_exp and req_exp <= max_exp:
			print("Exposure time within range...")
			print("Setting rspeed back to %s..." % (sys.argv[2]))
			os.system('rspeed %s' % (sys.argv[2]))
			print("Disabling FTest window...")
			os.system('window 1 disable')
			
			while j < int(sys.argv[1]):
				# take a flat at the last required exptime
				if sys.argv[2]=="fast":
					sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_f)
				if sys.argv[2]=="slow":
					sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_s)
				
				if req_exp > max_exp:
					print ("It's too dark, quiting!")
					break

				# if the median count are within range accept the flat
				# increase the counter and offset telescope for next flat
				if sky_lvl > min_counts and sky_lvl < max_counts:
					j=j+1
					print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[1]),t))
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
		os.system('window 1 "[800:1200,2400:2800]"')
		os.system('rspeed fast')
		
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
				os.system('window 1 disable')
				print("Setting rspeed back to %s..." % (sys.argv[2]))
				os.system('rspeed %s' % (sys.argv[2]))
				break


		# if the required exp time is less than the minimum
		# loop checking the sky until it is in range
		while req_exp > max_exp:
			sky_lvl,req_exp=FTest(token,data_loc,bias_f)
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
			time.sleep(15)
		
		# when in range set the rspeed to that on commandline
		# disable the FTest window
		if req_exp >= min_exp and req_exp <= max_exp:
			print("Exposure time within range...")
			print("Setting rspeed back to %s..." % (sys.argv[2]))
			os.system('rspeed %s' % (sys.argv[2]))
			print("Disabling FTest window...")
			os.system('window 1 disable')
			
			while j < int(sys.argv[1]):
				# take a flat at the last required exptime
				if sys.argv[2]=="fast":
					sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_f)
				if sys.argv[2]=="slow":
					sky_lvl,req_exp,t=Flat(token,req_exp,data_loc,bias_s)
				
				if req_exp < min_exp:
					print ("It's too bright, quiting!")
					break
				
				# if the median count are within range accept the flat
				# increase the counter and offset telescope for next flat
				if sky_lvl > min_counts and sky_lvl < max_counts:
					j=j+1
					print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[1]),t))
					o1=Offset(j)
					if o1 != 0:
						print("Problem offsetting, exiting!\n")
						sys.exit()
						
				if req_exp >= min_exp:
					continue
			
			# reset telescope pointing to 0 0 for next filter
			o1=Offset(0)
				
				