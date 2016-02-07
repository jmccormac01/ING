"""
#########################################################

	cd /home/whtobs/acam/jmcc/under_development/autoflat/
	python autoflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]
	
It will then prioritse the order of the filters and take the flats
requested. If too bright/dark for a filter it will move to the next one
until all flats are taken or the sky is too bright/dark to continue.
A summary of the successful flats is printed at the end.
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
	Add comments to headers?
	"""
	A function to check the command line arguments
	***To be replaced with argparse later***
	
	@rtype: list
	@return returnval: 0 = OK, >0 = Problem
	@return DEBUG: 0 = Normal, 1 = Debugging mode
	@return camera_name: CCD camera name e.g. acam
	@return filters: list of filter names for flats
	"""
	# check command line args
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
	
	# check to see if the number of flats required is unreasonable
	
	# check rspeed commands are correct
	if sys.argv[3] != "fast" and sys.argv[3] != "slow":
		print "Rspeed request is INVALID! Enter fast or slow"
		returnval = returnval + 1 
	else:
		print "Rspeed request is valid..."
		
	# make checks for filter names

	return returnval, DEBUG, camera_name, filters
def subP(comm):
	"""
	A function to call subprocesses and dump the output 
	from the ICS so it doesn't clog up the screen
	
	@rtype: subprocess
	@return p: subprocess for a given command
	"""

	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p
	"""
	A function to wait for the CCD clocks to become idle
	
	@rtype: int
	@return 0 = ok
	"""

	"""
	A function to wait for the telescope to be tracking
	
	@rtype: int
	@return 0 = ok
	"""
	
	A function to wait for filter wheels to stop moving
	
	@rtype: int
	@return 0 = ok
	"""
	
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
					co = raw_input("Waiting on the ACAM mirror. Continue checking? [y/n]")

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
				print "Unexpected response while waiting for ACAM mirror, aborting!"
			if done == 0:
				return 0
		if mirror_in == "IN":
			print("ACAM mirror deplyed...")
			return 0
	"""
	A function to determine morning or afternoon
	
	@rtype: int
	@return token: 0 = Afternoon, 1 = Morning 
	"""

	"""
	A function to return today's data directory
	
	@rtype: string
	@return data_loc: /path/to/data/ e.g. /obsdata/whta/20140203
	"""

#	n_filt=len(sys.argv) - 4	
	"""
	A function to sort the filter list according to time of day
	Afternoon = Blue --> Red
	Morning = Red --> Blue
	
	@rtype: tuple
	@return flat_list: sorted filter list
	@return serial_list: sorted list of filter serial numbers
	@return bad_list: list of filters not recognised
	"""
	
			bad_list.append(f_list[i])
	"""
	A function to change the filters
	
	@rtype: int
	@return 0 = ok 
	"""

	"""
	A function to return the name of the last image taken
	
	@rtype: string
	@return t: last image name
	"""

	"""
	A function to measure the bias level
	
	@rtype: float
	@return bias_s: slow readout speed bias level
	@return bias_f: fast readout speed bias level 
	"""

		p=subP('rspeed %s fast' % camera_name)
		os.system('bias %s' % camera_name)
		os.system('bias %s' % camera_name)
	
	"""
	A function to quickly check the sky level using a small window on the CCD
	
	@rtype: float, float, int
	@return sky_lvl: median sky brightness in counts
	@return req_exp: the required exposure time for the next flat
	@return sat_count: counter for the number of saturated images, used to stop the script if too bright 
	"""
	
	req_exp=test_time/(sky_lvl/target_counts)
	
	# if within limits, fine
	if sky_lvl <= 64000:		
	
	# if outside limits afternoon and morning need done differently
	"""
	A function to take flat field images
	
	@rtype: float, float, string, int
	@return sky_lvl: median sky brightness in counts
	@return req_exp: the required exposure time for the next flat
	@return t: name of flat field image
	@return sat_count: counter for the number of saturated images, used to stop the script if too bright 
	"""

	if token == 1:
	
	# if within limits, fine. if not then morning and afternoon need handled differently	
	if sky_lvl <= 64000:
	if token == 1:
	A function to offset the telescope between flats
	
	@rtype: int
	@return 0 = ok
	"""
	"""
	A function to catch ctrl+c key presses and abort safely
	
	@rtype: int
	@return 0 = ok
	"""
	
		os.system('abort %s &' % camera_name)
		p=subP('setccd %s autoflat' % camera_name)
chkd,DEBUG,camera_name,filt_list=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()
# a list for filter name, image number and median counts to print summary at the end
filt_summ, im_summ, med_summ = [],[],[]
print("To quit and setup the instrument, type 'q'.")
print("Checking telescope is setup for %s..." % (camera_name))
if DEBUG == 0:
	setup = CheckTSSetup(camera_name)
	if setup != 0:
		print("Problem setting up the telescope for %s, exiting..." % (camera_name))
		sys.exit(0)

	data_loc=testdir
n_filt=len(filt_list)
	
	if DEBUG == 0:
		c1=ChangeFilter(filt_seq[i], serial_seq[i])
			p=subP('window acam 1 "[875:1275,1850:2250]"')
			p=subP('rspeed acam fast')
		
		# set device specific windows for FTest	
				bias_f,bias_s=GetBiasLevel(data_loc)
				bias_f=500.0
				bias_s=1000.0
		
			sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
		if DEBUG == 1:
			sky_lvl = 12000.0
			req_exp = 0.1
			sat_count = 0
		
			if filt_seq[i] == filt_seq[-1]:	
					p=subP('setccd %s autoflat' % camera_name)
				# leave the for loop
				break	
			sky_lvl=12000.0
			req_exp = 0.1
		
		while req_exp < min_exp:
				sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
			if DEBUG == 1:
				req_exp = req_exp + 0.1
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
				p=subP('setccd %s autoflat' % camera_name)
				# catch error?	
			if DEBUG == 1:
				req_exp = 10
			
			# while there are more flats to take,
				if sys.argv[3]=="fast" and DEBUG == 0:
				if DEBUG == 1:
					sky_lvl = 30000
					req_exp = req_exp + 10
					t="test.fits"
				
					# append filter, name and sky level to summary lists 
					filt_summ.append(filt_seq[i])
					im_summ.append(t)
					med_summ.append(sky_lvl)
					
						print("Offset to %d %d..." % (j*5, j*5))
						if DEBUG == 0:
							o1=Offset(j)
			if DEBUG == 0:
				o1=Offset(0)
			p=subP('window acam 1 "[875:1275,1850:2250]"')
			p=subP('rspeed acam fast')
		# set device specific windows for FTest	
		#if camera_name == 'pfip':
				bias_f,bias_s=GetBiasLevel(data_loc)
				bias_f=500.0
				bias_s=1000.0
						
			sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
		if DEBUG == 1:
			sky_lvl = 12000.0
			req_exp = 10.0
			sat_count = 0
					p=subP('setccd %s autoflat' % camera_name)
					# catch error?
			sky_lvl=2000
			req_exp = 150
				sky_lvl,req_exp,sat_count=FTest(token,data_loc,bias_f,sat_count)
				req_exp = req_exp - 10.0			
			print("[Sky Level]: %d counts - [Required Exptime]: %.2f sec - Waiting..." % (sky_lvl, req_exp))
				p=subP('setccd %s autoflat' % camera_name)
				# catch error?
			if DEBUG == 1:
				req_exp = 31
			
				print("Taking flat...")
				if DEBUG == 1:
					sky_lvl = 30000
					req_exp = req_exp - 10
					t="test.fits"
				
					# append filter, name and sky level to summary lists 
					filt_summ.append(filt_seq[i])
					im_summ.append(t)
					med_summ.append(sky_lvl)
					
						if DEBUG == 0:
							o1=Offset(j)
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
	