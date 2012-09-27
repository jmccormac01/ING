
#########################################################
#                                                       #
#                  autoflat WFC v1.1                    #
#                                                       #
#                    James McCormac                     #
#                                                       #
#########################################################
#
#   Revision History:	
#   v1.1   13/08/12 - fixed <2s bug for morning flats
#	
#   bugs   13/09/12 - first exp from Ftest in afternoon is ~twice as long as needed
#
#   To do:
#       Get filter names from WFC mimic add to filter db
#       Add windowed flats capability
#       Add binning capability



from datetime import date, timedelta
import os, os.path, sys, time
import pyfits as pf
import numpy as np

print("Modules loaded...")

# Global Varibales #

filt_sleep = 15.0
offset_sleep = 5.0
max_counts = 35000.0
target_counts = 30000.0
min_counts = 20000.0
max_exp = 120.0
min_exp = 2.0
am_tweak = 0.75
pm_tweak = 1.25


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

	f_db='/home/intobs/jmcc/FilterDB.txt'
	f=open(f_db,'r').readlines()

	name,BoN,cen_wave,width=[],[],[],[]

	for i in range(0,len(f)):
		name.append(f[i].split()[0])
		cen_wave.append(f[i].split()[1])
		width.append(f[i].split()[2])
		BoN.append(f[i].split()[3])
	
	#f_list=sys.argv[1:] 

	id_n,cwl_n,wl_n,id_b,cwl_b,wl_b=[],[],[],[],[],[]
	
	# create 2 lists for narrow and broad band filters
	for i in range(0,len(f_list)):
		for j in range(0,len(f)):
			if f_list[i] == name[j]:
				if BoN[j] == 'B':
					id_b.append(name[j])
					cwl_b.append(cen_wave[j])
					wl_b.append(width[j])
				if BoN[j] == 'N':
					id_n.append(name[j])
					cwl_n.append(cen_wave[j])
					wl_n.append(width[j])
	
	# sort the two lists
	if len(cwl_b) > 0:	
		x=list(zip(cwl_b,wl_b,id_b))
		x.sort()
		cwl_b,wl_b,id_b=zip(*x)

	if len(cwl_n) > 0:
		y=list(zip(cwl_n,wl_n,id_n))
		y.sort()
		cwl_n,wl_n,id_n=zip(*y)
	
	# afternoon	
	if token == 0:
		flat_list=list(id_n)+list(id_b)
		print("Afternoon filter order:")
		print(flat_list)

	# morning
	if token == 1:
		flat_list=list(id_b)[::-1]+list(id_n)[::-1]
		print("Morning filter order:")
		print(flat_list)
	
	return flat_list


def ChangeFilter(name):
	
	print("Changing filter to %s..." % (name))
	
	os.system('filter %s' % (name))
	time.sleep(filt_sleep)

	
	return 0	


def GetBiasLevel(data_loc):
	
	print("Getting fast and slow bias levels…")
	
	os.system('bias') 
	
	
	
	h=pf.open('%s/s1.fit' % (data_loc))
	data=h[1].data
	
	sky_lvl=np.median(np.median(data, axis=0))
	
	return bias_f, bias_s


def FTest(token,data_loc,bias_f):
	
	if token == 0:
		test_time = min_exp
		tweak=pm_tweak
	if token == 1:
		test_time = 10
		tweak=am_tweak		
	
	# test when at testscope
	os.system('glance %d' % (test_time))
	
	# code to get median counts from test image
	h=pf.open('%s/s1.fit' % (data_loc))
	data=h[1].data
	
	sky_lvl=np.median(np.median(data, axis=0))-bias_f
		
	if token == 0:
		req_exp=test_time/(sky_lvl/target_counts)*tweak
		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))

	if token == 1:
		if sky_lvl <= 64000:
			req_exp=test_time/(sky_lvl/target_counts)*tweak
			print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))

		if sky_lvl > 64000:
			req_exp=test_time*0.1
			if req_exp<min_exp:
				req_exp=min_exp
				print ("[Ftest] Sky level saturating, trying %.2f sec" % (req_exp))
		
	return sky_lvl, req_exp
	

def Flat(token,flat_time,data_loc,bias):
	
	os.system('flat %.2f' % (flat_time))
	
	time.sleep(3)
	
	q=os.listdir(data_loc)
	q.sort()
	
	im_list=[]
	for i in range(0,len(q)):
		if q[i][0] == 'r' and q[i][-4:] == '.fit':
			im_list.append(q[i])
	
	# choose the last image
	t=im_list[-1]
	
	h=pf.open('%s/%s' % (data_loc, t))
	
	# check counts in centre of image
	y=h[4].shape[0]/2
	x=h[4].shape[1]/2
	
	data=h[4].data[y-100:y+100,x-100:x+100]
		
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

# Main #

if len(sys.argv) < 4:
	print("USAGE: py3.2 autoflat_test.py num rspeed f1, f2,..., fn\n")
	sys.exit(1)
			
token = GetAMorPM()

data_loc=GetDataDir(token)
if data_loc==0:
	print("Error finding data folder, exiting!")
	sys.exit()
	
n_filt,filt_list=GetFilters()

# get name of filters as appear in WFC mimic
# add to FiltersDB.txt
#filt_seq=SortFilters(token,filt_list)

filt_seq=filt_list
	
for i in range(0,len(filt_seq)):
	
	j = 0	

	c1=ChangeFilter(filt_seq[i])
	if c1 != 0:
		print("Problem changing filter, exiting!\n")
		sys.exit()
	
	if token == 0:
		
		# set a window and fast readout speed
		print("Setting up FTest window and rspeed to fast...")
		os.system('window 1 "[900:1100,1900:2100]"')
		os.system('rspeed fast')
		
		# get the bias level in real time to acount for any slight changes
		bias_f,bias_s=GetBiasLevel(data_loc)
		
		# take an FTest image to check the sky level
		print("Checking sky level...")
		sky_lvl,req_exp=FTest(token,data_loc,bias_f)
	
		if req_exp > max_exp:
			print ("It's too dark, quiting!")
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
	

	if token == 1:
		
		# set a window and fast readout speed
		print("Setting up FTest window and rspeed to fast...")
		os.system('window 1 "[900:1100,1900:2100]"')
		os.system('rspeed fast')
		
		# get the bias level in real time to acount for any slight changes
		bias_f,bias_s=GetBiasLevel(data_loc)
		
		# take an FTest image to check the sky level
		print("Checking sky level...")
		sky_lvl,req_exp=FTest(token,data_loc,bias_f)

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
				
				# sky_lvl > 64000 and <-- removed to solve <2s issue at end of morning flats
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
				
				