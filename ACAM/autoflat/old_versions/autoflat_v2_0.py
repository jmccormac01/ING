#########################################################
#   v1.4   06/08/13  -  Fixed bug in saturating behaviour - JMCC PRS 
#   v1.5   16/08/13  -  Added am/pm_tweaks of 0.9 and 1.1, upped max counts to 40,000  
#                       Added PRS's subprocesses - needs tested on ICS 
#                       Added summary of all successfull flats printed at the end - JMCC
#	v2.0   20/11/13  -  Added more checks on command line arguments
#                       Added DEBUG mode, camera_list  	
#                       Removed GetFilters(), filters returned from check on command line
#                       Reversed the flat ordering to blue-->red in pm and vice versa 			
#
#   Add comments to headers?
	
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
	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p
#	n_filt=len(sys.argv) - 4	
		p=subP('rspeed %s fast' % camera_name)
		os.system('bias %s' % camera_name)
		os.system('bias %s' % camera_name)
	
	req_exp=test_time/(sky_lvl/target_counts)
	
	# if within limits, fine
	if sky_lvl <= 64000:		
	
	# if outside limits afternoon and morning need done differently
	if token == 1:
	
	# if within limits, fine. if not then morning and afternoon need handled differently	
	if sky_lvl <= 64000:
	if token == 1:
		os.system('abort %s &' % camera_name)
chkd,DEBUG,camera_name,filt_list=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()
# a list for filter name, image number and median counts to print summary at the end
filt_summ, im_summ, med_summ = [],[],[]
print("To quit and setup the instrument, type 'q'.")

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
	print("\n\n------------------------------")
	print("\tAutoflat Summary")
	print("------------------------------\n")
	for i in range(0,len(filt_summ)):
		print("%s   %s   %s" % (filt_summ[i],im_summ[i],med_summ[i]))
	print('\n\n')
		
	