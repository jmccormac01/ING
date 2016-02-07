"""
#########################################################

	cd /home/whtobs/acam/jmcc/under_development/domeflat/
	python domeflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]
	
It will then take the flats in the normal order (not really important for dome 
flats). If a filter has not been observed with before the script will determine 
the best combination of lamps for efficient dome flats.  

	For now I will comment out parts of autoflat not needed until after testing

	To do:
		test at WHT
		put the f_db and bias_db in the same place ans share them!

#domeflattime_db='/home/whtobs/acam/jmcc/under_development/autoflat/DomeFlatTimeDB.txt'
domeflattime_db='/Users/James/Documents/ING/Scripts/ACAM/autoflat/DomeFlatTimeDB.txt'
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
		print('\nUSAGE: python domeflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]\n')
		print("camera: instrument being used (acam only for now)")
		print("num_flats_per_filter: target number of flats in each filter")
		print("rspeed: readout speed of the CCD (fast or slow)")
		print("f1 f2 ... fn: names of filters for flats (automatically prioritised)")
		print('e.g. python domeflat.py acam 5 fast SlnZ SlnR SlnI"\n')
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
	A function to get the domeflat time and lamps 
	combination from the database.
	If no filter in database return None
	
	@param filt: the filter to check
	@param rspeed: the readout speed requested
	@rtype float,string
	"""
	
	f=open(domeflattime_db).readlines()
	
	for i in range(0,len(f)):
		name,fast,slow,lampcombo=f[i].split()
		if filt == name and rspeed == 'slow':
			return float(slow), lampcombo
		elif filt == name and rspeed == 'fast':
			return float(fast), lampcombo
		else:
			return None, None


def SwitchOffLamps():
	
	# switch off lamps
	
	return 0


	
	# switch off all the lamps
	off=SwitchOffLamps()
	
	# turn on the ones needed	
	lamplist=lampcombo.split(',')
	
	if '9W=On' in lamplist:
		# switch on 9W
	if '25W=On' in lamplist:
		# switch on 25W	
	if '150W=On' in lamplist:
		# switch on 150W	
	if '500W=On' in lamplist:
		# switch on 500W	
	if '500W=On' in lamplist:
		# switch on 500W
		
	return 0
	"""
	A function to catch ctrl+c key presses and abort safely
	
	@rtype: int
	@return 0 = ok
	"""
	
		os.system('abort %s &' % camera_name)
		os.system('setccd %s domeflat' % camera_name)
chkd,DEBUG,camera_name,filt_list=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()
# a list for filter name, image number and median counts to print summary at the end
filt_summ, im_summ, med_summ = [],[],[]
print("It is also assumed that the telescope is pointed at the dome flat position")
print("and the mirror petals are open. To QUIT and setup the instrument, type 'q'.")
print("Checking telescope is setup for %s..." % (camera_name))
if DEBUG == 0:
	setup = CheckTSSetup(camera_name)
	if setup != 0:
		print("Problem setting up the telescope for %s, exiting..." % (camera_name))
		sys.exit(0)
	data_loc=testdir
n_filt=len(filt_list)
	sat_count = 0 # reset the sat_count value for each filter
	
	if DEBUG == 0:
		c1=ChangeFilter(filt_seq[i], serial_seq[i])
	
	# get the dome flat times from database
	print("Checking for known domeflat time...")
	if DEBUG == 0:
		dtime,lampcombo=GetDomeFlatTime(filt_seq[i],sys.argv[3])
	else:
		dtime = 10
		lampcombo='9W=On,25W=Off,150W=Off,500W=Off,500W=Off'
		
	if dtime == None and lampcombo == None:
		print("Domeflat times not calculated for filter %s" %(filt_seq[i]))
		print("Do so manually then add the setup to: ")
		print("%s" % (domeflattime_db))
	
	else:
		# turn on the lamps
		print('Switching on the lamps...')
		if DEBUG == 0:
			on=SwitchOnLamps(lampcombo)	
		
	print("Taking flats...")
	if DEBUG == 0:		
		os.system('multflat %s %s %d "DomeFlat %s"' % (camera_name,sys.argv[2],sky_lvl,filt_seq[i]))
	
	# if its the last filter, quit
	if filt_seq[i] == filt_seq[-1]:	
		print("Switching lamps off...")
		if DEBUG == 0:
			off=SwitchLampsOff()			
		break	
	