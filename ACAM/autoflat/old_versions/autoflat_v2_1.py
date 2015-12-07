"""
##########################################################                                                       ##                    autoflat v2.1                   	##                                                       ##          James McCormac & Patrick Sandquist           ##                                                       ##########################################################To run this script type:

	cd /home/whtobs/acam/jmcc/under_development/autoflat/
	python autoflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]
	
It will then prioritse the order of the filters and take the flats
requested. If too bright/dark for a filter it will move to the next one
until all flats are taken or the sky is too bright/dark to continue.
A summary of the successful flats is printed at the end.Revision History:		v1.0	27/06/13	- Original script editted to include a camera command - JMCC	v1.1	26/06/13	- Functions added to optimise speed on a variety of cameras - PRS	v1.2	15/07/13	-  Script tested at the telescope several bugs corrected - JMCC	v1.3	20/07/13	-  Added new save/setccd functionality, plus <min_exp_time flat fix - PRS		20/07/13	- Fixed some coding errors with the save/setccd calls, to be tested on sky - JMCC  	
	v1.4	06/08/13	- Fixed bug in saturating behaviour - JMCC PRS 
	v1.5	16/08/13	- Added am/pm_tweaks of 0.9 and 1.1, upped max counts to 40,000  
		16/08/13	- Added PRS's subprocesses - needs tested on ICS 
		16/08/13	- Added summary of all successfull flats printed at the end - JMCC
	v2.0	20/11/13	- Added more checks on command line arguments
		20/11/13	- Added DEBUG mode, camera_list  	
		20/11/13	- Removed GetFilters(), filters returned from check on command line
		20/11/13	- Reversed the flat ordering to blue-->red in pm and vice versa 			
	v2.1	17/01/14	- Added check for agmirror and setccd to abort function
		17/01/14	- Found sat_count bug, reset for each filter now
		17/01/14	- Added bad_list for filters not done to summary

	To do:
	Add comments to headers?	Update filter database"""import sys, subprocess, signal, os, os.path, timefrom datetime import date, timedeltaimport pyfits as pfimport numpy as npprint("Modules loaded...")# Global Varibales ## Check to see if camera is in the database, then load the appropriate variable valuesmax_counts = 40000.0target_counts = 30000.0min_counts = 15000.0max_exp = 120.0min_exp = 0.5am_tweak = 0.90pm_tweak = 1.10fast_slow_gain=2.02chip=1# WFC# fast_slow_gain = 1.95# min_exp = 2.0# am_tweak = 0.70# pm_tweak = 1.25testdir = '~/Documents/ING/Scripts/ACAM/autoflat/test'f_db='/home/whtobs/acam/jmcc/under_development/autoflat/FilterDB.txt'#f_db='/Users/James/Documents/ING/Scripts/ACAM/autoflat/FilterDB.txt'bias_db='/home/whtobs/acam/jmcc/under_development/autoflat/BiasLevelDB.txt'camera_list=['acam']sat_count = 0# Functions #def CheckCommandLine():
	"""
	A function to check the command line arguments
	***To be replaced with argparse later***
	
	@rtype: list
	@return returnval: 0 = OK, >0 = Problem
	@return DEBUG: 0 = Normal, 1 = Debugging mode
	@return camera_name: CCD camera name e.g. acam
	@return filters: list of filter names for flats
	"""
	# check command line args	# make more detailed when FilterDB is full	
	if len(sys.argv) < 5:
		print('\nUSAGE: python autoflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]\n')
		print("camera: instrument being used (acam only for now)")
		print("num_flats_per_filter: target number of flats in each filter")
		print("rspeed: readout speed of the CCD (fast or slow)")
		print("f1 f2 ... fn: names of filters for flats (automatically prioritised)")
		print('e.g. python autoflat.py acam 5 fast SlnZ SlnR SlnI"\n')
		exit()
	
	returnval = 0
	fs=0
	
	# check DEBUG and/or TEST
	if 'DEBUG' in sys.argv or 'debug' in sys.argv:
		DEBUG = 1
		fs = fs - 1 
		print "\n*************************************************"
		print "************ ENTERING DEBUGGING MODE ************"
		print "*** NO IMAGES WILL BE TAKEN. SIMULATION ONLY! ***"
		print "*************************************************\n"
	else:	
		DEBUG = 0
	
	# make check for TEST		
	
	# check camera name is valid
	if sys.argv[1] not in camera_list:
		print("Camera name is INVALID!")
		print("Available cameras: ")
		for i in range(0,len(camera_list)):
			print("\t%s" % (camera_list[i]))
		returnval = returnval + 1
	if sys.argv[1] in camera_list:
		camera_name = sys.argv[1]
	
	# check number of flats is integer
	try:
		int(sys.argv[2])
	except ValueError:
		print("Image number is INVALID!")
		returnval = returnval + 1
	else:
		print("Image number is valid...")
		
	
	if DEBUG == 0:
		filters=sys.argv[4:]
	if DEBUG == 1:
		filters=sys.argv[4:-1]
	
	# check to see if the number of flats required is unreasonable	num_flats_tot=(len(filters))*int(sys.argv[2])	if num_flats_tot> 40:	# if the total number of flats is rather large,		print("You've asked for a total of (%dx%d) %d flats" % (int(sys.argv[2]),len(filters),num_flats_tot))		contin = raw_input("Are you sure you want to continue? [y/n]")		if contin != 'y' and contin != 'Y':			print("Exiting!!")			sys.exit(1)
	
	# check rspeed commands are correct
	if sys.argv[3] != "fast" and sys.argv[3] != "slow":
		print "Rspeed request is INVALID! Enter fast or slow"
		returnval = returnval + 1 
	else:
		print "Rspeed request is valid..."
		
	# make checks for filter names

	return returnval, DEBUG, camera_name, filters# subprocess - to stop the annoying output from the ICS when changing rspeed etc
def subP(comm):
	"""
	A function to call subprocesses and dump the output 
	from the ICS so it doesn't clog up the screen
	
	@rtype: subprocess
	@return p: subprocess for a given command
	"""

	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p# Returns zero when the camera is idledef WaitForIdle():
	"""
	A function to wait for the CCD clocks to become idle
	
	@rtype: int
	@return 0 = ok
	"""
	idle=""	counter = 0	while idle != "idling":		if camera_name == 'acam': 			idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]		#if camera_name == 'pfip':		#	do x y z				time.sleep(1)		counter += 1				if idle == "idling":			return 0				if counter == 30: # large enough?			co = raw_input("%s is not idle. Continue checking? [y/n]" % camera_name)			if co == 'n' or co == 'N' or co == 'q' or co == 'Q':				print("Exiting!!")				sys.exit(1)			counter = 0# Returns zero when the telescope is trackingdef WaitForTracking():
	"""
	A function to wait for the telescope to be tracking
	
	@rtype: int
	@return 0 = ok
	"""
		stat=""	counter = 0	while stat != "TRACKING":		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]				time.sleep(1)		counter += 1				if stat == "TRACKING":			return 0				if counter == 30:			co = raw_input("The telescope is not tracking. Continue checking? [y/n]")			if co == 'n' or co == 'N' or co == 'q' or co == 'Q':				print("Exiting!!")				sys.exit(1)			counter = 0# Returns zero when the filter wheel is ready (only works for one filter being in place!)def WaitForFilterWheels(required_filter_serial_num):	"""
	A function to wait for filter wheels to stop moving
	
	@rtype: int
	@return 0 = ok
	"""
		required_filter_serial_num=str(required_filter_serial_num) # needs to be a string for the later comparison	counter = 0	while (1):		wheel1_serial_num = os.popen('ParameterNoticeBoardLister -i CAGB.WHB.SERIALNUMBER').readline().split('\n')[0]		wheel2_serial_num = os.popen('ParameterNoticeBoardLister -i CAGB.WHA.SERIALNUMBER').readline().split('\n')[0]		wheel1_opticalelementtype = os.popen('ParameterNoticeBoardLister -i CAGB.WHB.OPTICALELEMENTTYPE').readline().split('\n')[0]		wheel2_opticalelementtype = os.popen('ParameterNoticeBoardLister -i CAGB.WHA.OPTICALELEMENTTYPE').readline().split('\n')[0]						if wheel2_serial_num == required_filter_serial_num and wheel1_opticalelementtype == "UNKNOWN" or wheel1_serial_num == required_filter_serial_num and wheel2_opticalelementtype == "UNKNOWN":			return 0		else:			time.sleep(1)			counter += 1			if counter == 30: 				co = raw_input("Waiting on the filter wheel to rotate. Continue checking? [y/n]")				if co == 'n' or co == 'N' or co == 'q' or co == 'Q':					print("Exiting!!")					sys.exit(1)				counter = 0# ADD!!!
def WaitForFocus():
	"""
	A function to wait for the telescope focus to have settled
	***Not yet implemented***
	
	@rtype: int
	@return 0 = ok
	"""

	return 0
def WaitForMirror(camera_name):
	"""
	A function to wait for the A&G box mirror
	
	@rtype: int
	@return 0 = ok
	"""
	
	counter = 0
	
	# check for agacam
	if camera_name == 'acam':
		while (1):
			mirror_in=os.popen('ParameterNoticeBoardLister -i AGCA.FLF.Position').readline().split('\n')[0]
			if mirror_in == "IN":
				return 0	
			else:
				time.sleep(1)
				counter += 1
				if counter == 30:
					co = raw_input("Waiting on the ACAM mirror. Continue checking? [y/n]")					if co == 'n' or co == 'N' or co == 'q' or co == 'Q':						print("Exiting!!")						sys.exit(1)					counter = 0	
def CheckTSSetup(camera_name):
	"""
	A function to check the telescope is setup for the right camera
	
	@rtype: int
	@return 0 = ok
	"""
	
	# check that telescope is setup for given instrument
	# add mirror petals if possible
	
	# check for agacam
	if camera_name == 'acam':
		mirror_in=os.popen('ParameterNoticeBoardLister -i AGCA.FLF.Position').readline().split('\n')[0]
		
		if mirror_in == "OUT":
			print("ACAM mirror not deployed, deploying...")
			p=subP('agacam')
			done=WaitForMirror(camera_name)
			if done != 0:
				print "Unexpected response while waiting for ACAM mirror, aborting!"				os.system('abort %s &' % camera_name)				sys.exit(1)
			if done == 0:
				return 0
		if mirror_in == "IN":
			print("ACAM mirror deplyed...")
			return 0def GetAMorPM():
	"""
	A function to determine morning or afternoon
	
	@rtype: int
	@return token: 0 = Afternoon, 1 = Morning 
	"""
	h_now=int(time.ctime().split()[3].split(':')[0])	# finds the current hour	if h_now >= 12:		print("Afternoon Flats...")		token=0		# token is zero for the afternoon	if h_now < 12:		print("Morning Flats...")		token=1		# token is 1 for the morning	return tokendef GetDataDir(token):
	"""
	A function to return today's data directory
	
	@rtype: string
	@return data_loc: /path/to/data/ e.g. /obsdata/whta/20140203
	"""
	d=date.today()-timedelta(days=token)	# time of last data recorded?	x="%d%02d%02d" % (d.year,d.month,d.day)	if os.path.exists("/obsdata/whta/%s" % (x)) == True:	# looks for the data directory		data_loc="/obsdata/whta/%s" % (x)	elif os.path.exists("/obsdata/whtb/%s" % (x)) == True:		data_loc="/obsdata/whtb/%s" % (x)	else:		data_loc =0	return data_loc	# obsolete	#def GetFilters():
#	n_filt=len(sys.argv) - 4	#	if n_filt >= 1:				# if there are filters being used,#		filt_list=sys.argv[4:]	# fill filt_list with the names given in the argv (from 3 to the end)#		print("Filter(s): %s" % filt_list)#	return n_filt, filt_listdef SortFilters(token,f_list):
	"""
	A function to sort the filter list according to time of day
	Afternoon = Blue --> Red
	Morning = Red --> Blue
	
	@rtype: tuple
	@return flat_list: sorted filter list
	@return serial_list: sorted list of filter serial numbers
	@return bad_list: list of filters not recognised
	"""
		f=open(f_db,'r').readlines()	# open the filter database and read all the lines into f	name,BoN,cen_wave,width,num,mimic,bad_list=[],[],[],[],[],[],[]	# create lists for the variables	for i in range(0,len(f)):	# for each of the filters in the database,		name.append(f[i].split()[0])	# add the filter names to the name list		cen_wave.append(f[i].split()[1])# add the center wavelength to the correct list		width.append(f[i].split()[2])	# beam width		BoN.append(f[i].split()[-1]) 	# broad or narrow character		num.append(f[i].split()[3])		# the filter number		mimic.append(f[i].split()[4])	# the filter discription		id_n,cwl_n,wl_n,id_b,cwl_b,wl_b,num_b,num_n=[],[],[],[],[],[],[],[]		# create 2 lists for narrow and broad band filters	for i in range(0,len(f_list)):	# for each of the filters that the user wants to use,		for j in range(0,len(f)):	# for each of the filters in the database,			if f_list[i] == name[j]:	# if the desired filter is in the database,				if BoN[j] == 'B':		# add the properties to the correct list					id_b.append(name[j])					cwl_b.append(cen_wave[j])					wl_b.append(width[j])					num_b.append(num[j])				if BoN[j] == 'N':					id_n.append(name[j])					cwl_n.append(cen_wave[j])					wl_n.append(width[j])					num_n.append(num[j])				if f_list[i] not in name:			print("Filter not found: %s" % (f_list[i]))
			bad_list.append(f_list[i])				# sort the two lists	if len(cwl_b) > 0:	# if there are filters in the broad lists,			x = list(zip(cwl_b,wl_b,id_b,num_b))	# make list x which contains all of the information (filter properties are grouped together)		x.sort(reverse = True)	# sort the list (will be sorted by central wavelength (blue to red) while maintaining the filter grouping)		cwl_b,wl_b,id_b,num_b=zip(*x)	# unzips the list sorted by central wavelength	if len(cwl_n) > 0:		y=list(zip(cwl_n,wl_n,id_n,num_n))		y.sort(reverse = True)		cwl_n,wl_n,id_n,num_n=zip(*y)		# test using filters in reverse order	# afternoon		if token == 0:		flat_list=list(id_n)[::-1]+list(id_b)[::-1]	# make flats list by narrows then broads (id_n and id_b are sorted from blue to red)		serial_list=list(num_n)[::-1]+list(num_b)[::-1]	# make serial number list arranged n to b sorted by wavelength		print("Afternoon filter order:")		print(flat_list)	# morning	if token == 1:		flat_list=list(id_b)+list(id_n)	# flats list arranged broad then narrow (both red to blue)		serial_list=list(num_b)+list(num_n)	# serial number list arranged b to n by wavelength		print("Morning filter order:")		print(flat_list)		return (flat_list, serial_list, bad_list)def ChangeFilter(name, serial_number):
	"""
	A function to change the filters
	
	@rtype: int
	@return 0 = ok 
	"""
	print("Changing filter to %s..." % (name))	if camera_name == 'acam': # change for other cameras		os.system('acamimage %s' % name)		# check to see if the filter wheel is ready	ready = WaitForFilterWheels(serial_number)	if ready != 0:		print "Unexpected response while waiting for the filter wheels, aborting!"		os.system('abort %s &' % camera_name)	return 0def GetLastImage(data_loc):
	"""
	A function to return the name of the last image taken
	
	@rtype: string
	@return t: last image name
	"""
	q=os.listdir(data_loc)	# a list of the names of the entries in data_loc directory	q.sort()	# sort the list (alpha numeric)		im_list=[]	for i in range(0,len(q)):	# for each entry in the directory,		if q[i][0] == 'r' and q[i][-4:] == '.fit':	# if the first chracter in the string is 'r' and the last 4 are '.fit',			im_list.append(q[i])	# add the filename to the new list	# choose the last image (the most recent)	t=im_list[-1]	return t# add to save bias to file and check there first for the current daydef GetBiasLevel(data_loc):
	"""
	A function to measure the bias level
	
	@rtype: float
	@return bias_s: slow readout speed bias level
	@return bias_f: fast readout speed bias level 
	"""
	print("Getting fast and slow bias levels")		# BiasLevelDB.txt e.g. format:	# 6 Mar 2013 bias_s bias_f		# check the BiasLevelDB.txt file for bias levels first	lday,lmonth,lyear,lbias_s,lbias_f=open(bias_db).readlines()[-1].split()[:5]	# from the last line of the bias file, split the line and add to the appropriate lists		# get date now	now=time.ctime()	day = now.split()[2]	month = now.split()[1]	year = now.split()[-1]		# compare to last date from log, if different work out the bias level again	# if the day is the same just use what is in the database	if lday == day and lmonth == month and lyear == year:	# if the day is the same,		print('Bias levels in database, using these values...')		bias_s = float(lbias_s)	# use the information from the database (float converts from string to float)		bias_f = float(lbias_f)			if lday != day or lmonth != month or lyear != year:	# if there is no bias level in the database,				print('No bias levels in database, taking bias images to check...')				# fast		#os.system('rspeed %s fast' % camera_name)
		p=subP('rspeed %s fast' % camera_name)
		os.system('bias %s' % camera_name)				time.sleep(1)				t=GetLastImage(data_loc)				h=pf.open('%s/%s' % (data_loc,t))		data=h[1].data				bias_f=np.median(np.median(data, axis=0))	# finds the median value of rows and then columns				# slow		#os.system('rspeed %s slow' % camera_name)		p=subP('rspeed %s slow' % camera_name)
		os.system('bias %s' % camera_name)				time.sleep(1)				t2=GetLastImage(data_loc)				h2=pf.open('%s/%s' % (data_loc,t2))		data2=h2[1].data				bias_s=np.median(np.median(data2, axis=0))				print("Bias Slow: %.2f ADU" % (bias_s))		print("Bias Fast: %.2f ADU" % (bias_f))				# save the bias levels to the BiasLevelDB.txt		f=open(bias_db,'a')		f.write("%s  %s  %s  %s  %s\n" % (day,month,year,bias_s,bias_f))		f.close()				# set rspeed to fast again for FTest		#os.system('rspeed %s fast' % camera_name)		p=subP('rspeed %s fast' % camera_name)
		return bias_f, bias_s# take a test image of the centre of the CCD to save timedef FTest(token,data_loc,bias_f,sat_count):
	"""
	A function to quickly check the sky level using a small window on the CCD
	
	@rtype: float, float, int
	@return sky_lvl: median sky brightness in counts
	@return req_exp: the required exposure time for the next flat
	@return sat_count: counter for the number of saturated images, used to stop the script if too bright 
	"""
		if token == 0:	# afternoon		test_time = 0.5	if token == 1:	# morning		test_time = 10.0		# test when at testscope	os.system('glance %s %f' % (camera_name,test_time)) 		idle=WaitForIdle() # check to see if the camera is idle	if idle != 0:		print "Unexpected response while waiting for CCD to idle, aborting!"		os.system('abort %s &' % camera_name)		exit()		# code to get median counts from test image	h=pf.open('%s/s1.fit' % (data_loc))	data=h[1].data		sky_lvl=np.median(np.median(data, axis=0))-bias_f	# take the median of the image and subtract the bias level (a median) to obtain the sky level	
	req_exp=test_time/(sky_lvl/target_counts)
	
	# if within limits, fine
	if sky_lvl <= 64000:				# account for gain difference between fast and slow rspeeds		if sys.argv[3] == 'slow':			req_exp=req_exp/fast_slow_gain		sat_count = 0
	
	# if outside limits afternoon and morning need done differently	if token == 0:	# afternoon		if sky_lvl > 64000 or req_exp<min_exp:			print ("[Ftest] Sky level saturating...")		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))			if token == 1:	# morning		if sky_lvl > 64000:			req_exp=min_exp			print ("[Ftest] Sky level saturating...")			sat_count = sat_count + 1				print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))		return sky_lvl, req_exp, sat_count# take the flat imagedef Flat(token,flat_time,data_loc,bias,sat_count):
	"""
	A function to take flat field images
	
	@rtype: float, float, string, int
	@return sky_lvl: median sky brightness in counts
	@return req_exp: the required exposure time for the next flat
	@return t: name of flat field image
	@return sat_count: counter for the number of saturated images, used to stop the script if too bright 
	"""
	# tell system to take a flat	os.system('flat %s %.2f' % (camera_name,flat_time))		idle=WaitForIdle() # check that the camera is idle	if idle != 0:		print "Unexpected response while waiting for CCD to idle, aborting!"		os.system('abort %s &' % camera_name)		exit()	t=GetLastImage(data_loc)	h=pf.open('%s/%s' % (data_loc, t))[chip].data		# check counts in centre of image	y=h.shape[0]/2.0	x=h.shape[1]/2.0		data=h[y-100:y+100,x-100:x+100]	# data is the 200x200 box centred at the origin		sky_lvl=np.median(np.median(data, axis=0))-bias		# subtract the bias		# tweak the required exptime to stop rising and	# falling counts during calibration phase to account for change between when image is taken and read off	if token == 0:		tweak=pm_tweak
	if token == 1:		tweak=am_tweak
	
	# if within limits, fine. if not then morning and afternoon need handled differently	
	if sky_lvl <= 64000:		req_exp=(flat_time/(sky_lvl/target_counts))*tweak		print("[Flat: %s] Sky Level: %d Required Exptime: %.2f" % (t,int(sky_lvl),req_exp))		if token == 0:		if sky_lvl > 64000 or req_exp<min_exp:			print ("[Ftest] Sky level saturating....")			sat_count = sat_count + 1	
	if token == 1:		if sky_lvl > 64000:			req_exp=min_exp			print ("[Flat: %s] Sky level saturating...")			sat_count = sat_count + 1		return sky_lvl,req_exp,t,sat_countdef Offset(j):	"""
	A function to offset the telescope between flats
	
	@rtype: int
	@return 0 = ok
	"""	shift=j*5	os.system('offset arc %d %d' % (shift, shift))		done=WaitForTracking()	if done != 0:		print "Unexpected response while waiting for telescope to resume tracking, aborting!"		os.system('abort %s &' % camera_name)		sys.exit(1)		return 0################################################################ Ctrl + C Trapping ###################################################################def signal_handler(signal, frame):
	"""
	A function to catch ctrl+c key presses and abort safely
	
	@rtype: int
	@return 0 = ok
	"""
		print('   Ctrl+C caught, shutting down...')	if DEBUG == 0:
		os.system('abort %s &' % camera_name)
		p=subP('setccd %s autoflat' % camera_name)	sys.exit(0)signal.signal(signal.SIGINT, signal_handler)###################################################### Main ####################################################### make checks on all the numbers!
chkd,DEBUG,camera_name,filt_list=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()# summary lists
# a list for filter name, image number and median counts to print summary at the end
filt_summ, im_summ, med_summ = [],[],[]# Begin by making sure that the user is ready to take flatsprint("\nIt is assumed that the instrument, CCD, and windows are set up correctly.")
print("To quit and setup the instrument, type 'q'.")contin = raw_input("Press return to proceed.\n")if contin == 'n' or contin == 'N' or contin == 'q' or contin == 'Q':	print("Exiting!!")	sys.exit(0)# check the T/S is setup correctly for flats
print("Checking telescope is setup for %s..." % (camera_name))
if DEBUG == 0:
	setup = CheckTSSetup(camera_name)
	if setup != 0:
		print("Problem setting up the telescope for %s, exiting..." % (camera_name))
		sys.exit(0)# Save the current settings of the CCD to a temporary file#os.system('saveccd %s autoflat' % camera_name)if DEBUG == 0:	p=subP('saveccd %s autoflat' % camera_name)
# get afternoon or morning			token = GetAMorPM()# get tonights folderif DEBUG == 0:	data_loc=GetDataDir(token)	if data_loc==0:		print("Error finding data folder, exiting!")		sys.exit()if DEBUG == 1:
	data_loc=testdir	# get the list of filters	#n_filt,filt_list=GetFilters() # Obsolete
n_filt=len(filt_list)# sort the filtersfilt_seq, serial_seq, bad_list = SortFilters(token,filt_list)# begin looping over required number of flats	for i in range(0,len(filt_seq)):	j = 0	# what number flat we are on	sat_count = 0 # reset the sat_count value for each filter
		# change to new filter	print("\nChanging filter to %s [%s]..." % (filt_seq[i],serial_seq[i]))
	if DEBUG == 0:
		c1=ChangeFilter(filt_seq[i], serial_seq[i])		if c1 != 0:			print("Problem changing filter, exiting!\n")			sys.exit()		# afternoon	if token == 0:		print("Setting up FTest window and rspeed to fast...")		if camera_name == 'acam' and DEBUG == 0:
			p=subP('window acam 1 "[875:1275,1850:2250]"')
			p=subP('rspeed acam fast')
		
		# set device specific windows for FTest			#if camera_name == 'pfip':			# add more			# get the bias level in real time to account for any slight changes		if i == 0:	# do for first flat only			if DEBUG == 0:
				bias_f,bias_s=GetBiasLevel(data_loc)			if DEBUG == 1:
				bias_f=500.0
				bias_s=1000.0
				# take an FTest image to check the sky level		print("Checking sky level...")		if DEBUG == 0:
			sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
		if DEBUG == 1:
			sky_lvl = 12000.0
			req_exp = 0.1
			sat_count = 0
				if req_exp > max_exp:			print ("It's too dark for this filter, next!")			# if on the last filter return CCD to previous state
			if filt_seq[i] == filt_seq[-1]:					print ("No filters left, quiting!")				print("Disabling FTest window...")				print("Reseting CCD to observing mode")				if DEBUG == 0:
					p=subP('setccd %s autoflat' % camera_name)				
				# leave the for loop
				break			# if the required exp time is less than the minimum (sky too bright)		# loop checking the sky until it is in range		if DEBUG == 1:
			sky_lvl=12000.0
			req_exp = 0.1
		
		while req_exp < min_exp:			if DEBUG == 0:
				sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
			if DEBUG == 1:
				req_exp = req_exp + 0.1
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))			time.sleep(15)				# when in range set the rspeed to that on commandline		# disable the FTest window		if req_exp >= min_exp and req_exp <= max_exp:			print("Exposure time within range...")			print("Reseting CCD to observing mode")			if DEBUG == 0:
				p=subP('setccd %s autoflat' % camera_name)
				# catch error?							
			if DEBUG == 1:
				req_exp = 10
			
			# while there are more flats to take,			while j < int(sys.argv[2]):					# take a flat at the last required exptime				print "Taking flat..."
				if sys.argv[3]=="fast" and DEBUG == 0:					sky_lvl,req_exp,t,sat_count = Flat(token,req_exp,data_loc,bias_f,sat_count)				if sys.argv[3]=="slow" and DEBUG == 0:					sky_lvl,req_exp,t,sat_count = Flat(token,req_exp,data_loc,bias_s,sat_count)				
				if DEBUG == 1:
					sky_lvl = 30000
					req_exp = req_exp + 10
					t="test.fits"
								if req_exp > max_exp:					print ("It's too dark, quiting!")					break				# if the median count are within range accept the flat				# increase the counter and offset telescope for next flat				if sky_lvl > min_counts and sky_lvl < max_counts:					j=j+1					print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[2]),t))					
					# append filter, name and sky level to summary lists 
					filt_summ.append(filt_seq[i])
					im_summ.append(t)
					med_summ.append(sky_lvl)
										# dont offset for the final image of a filter					if j < int(sys.argv[2]):
						print("Offset to %d %d..." % (j*5, j*5))
						if DEBUG == 0:
							o1=Offset(j)							if o1 != 0:								print("Problem offsetting, exiting!\n")								sys.exit()								if sat_count >= 2:					sat_count = 0					break 									if req_exp <= max_exp:					continue							# reset telescope pointing to 0 0 for next filter			print("Offset to 0 0...")
			if DEBUG == 0:
				o1=Offset(0)		# morning	if token == 1:				# set a window and fast readout speed		print("Setting up FTest window and rspeed to fast...")		if camera_name == 'acam' and DEBUG == 0:
			p=subP('window acam 1 "[875:1275,1850:2250]"')
			p=subP('rspeed acam fast')		
		# set device specific windows for FTest	
		#if camera_name == 'pfip':			# add more			# get the bias level in real time to acount for any slight changes		# do for first flat only			if i == 0:			if DEBUG == 0:
				bias_f,bias_s=GetBiasLevel(data_loc)			if DEBUG == 1:
				bias_f=500.0
				bias_s=1000.0
								# take an FTest image to check the sky level		print("Checking sky level...")		if DEBUG == 0:
			sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
		if DEBUG == 1:
			sky_lvl = 12000.0
			req_exp = 10.0
			sat_count = 0		# sky_lvl > 64000 and <-- removed to solve <2s issue at end of morning flats		if req_exp < min_exp:			print ("It's too bright for this filter, next!")			if filt_seq[i] == filt_seq[-1]:				print ("No filters left, quiting!")				print("Disabling FTest window...")				print("Reseting CCD to observing mode")				if DEBUG == 0:
					p=subP('setccd %s autoflat' % camera_name)
					# catch error?					# leave the for loop							break		if DEBUG == 1:
			sky_lvl=2000
			req_exp = 150		# if the required exp time is less than the minimum		# loop checking the sky until it is in range		while req_exp > max_exp:	# sky is too dark			if DEBUG == 0:
				sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)			if DEBUG == 1:
				req_exp = req_exp - 10.0			
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))			time.sleep(15)				# when in range set the rspeed to that on commandline		# disable the FTest window		if req_exp >= min_exp and req_exp <= max_exp:			print("Exposure time within range...")			print("Reseting CCD to observing mode")			if DEBUG == 0:
				p=subP('setccd %s autoflat' % camera_name)
				# catch error?			
			if DEBUG == 1:
				req_exp = 31
						while j < int(sys.argv[2]):									if req_exp < min_exp:					print ("It's too bright to take flat, quiting!")					break				if req_exp > max_exp:					print ("It's too dark to take flat, quiting!")					break								
				print("Taking flat...")				# take a flat at the last required exptime				if sys.argv[3]=="fast" and DEBUG == 0:					sky_lvl,req_exp,t,sat_count=Flat(token,req_exp,data_loc,bias_f,sat_count)				if sys.argv[3]=="slow" and DEBUG == 0:					sky_lvl,req_exp,t,sat_count=Flat(token,req_exp,data_loc,bias_s,sat_count)				
				if DEBUG == 1:
					sky_lvl = 30000
					req_exp = req_exp - 10
					t="test.fits"
								# if the median count are within range accept the flat				# increase the counter and offset telescope for next flat				if sky_lvl > min_counts and sky_lvl < max_counts:					j=j+1	# go to next flat					print("[%d/%d] Flat %s successful..." % (int(j),int(sys.argv[2]),t))					
					# append filter, name and sky level to summary lists 
					filt_summ.append(filt_seq[i])
					im_summ.append(t)
					med_summ.append(sky_lvl)
										# don't offset for the final image of a filter					if j < int(sys.argv[2]):						print("Offset to %d %d..." % (j*5, j*5))
						if DEBUG == 0:
							o1=Offset(j)							if o1 != 0:								print("Problem offsetting, exiting!\n")								sys.exit()								if sat_count >= 2:					sat_count = 0					break					if req_exp >= min_exp:					continue												# reset telescope pointing to 0 0 for next filter			print("Offset to 0 0...")
			if DEBUG == 0:
				o1=Offset(0)
			
# print out the summary
if len(filt_summ) == len(im_summ) == len(med_summ):
	print("\n--------------------------------")
	print("\tAutoflat Summary")
	print("--------------------------------")
	for i in range(0,len(filt_summ)):
		print("%s   %s   %s" % (filt_summ[i],im_summ[i],med_summ[i]))
	if len(bad_list) > 0:
		print("\n--------------------------------")
		print("\tFILTERS *NOT* DONE")
		print("--------------------------------")
		for i in range(0,len(bad_list)):
			print "%s" % (bad_list[i])
	print('\n\n')
	