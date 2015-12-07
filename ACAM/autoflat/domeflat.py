"""
##########################################################                                                       ##                    domeflat v1.0                   	##                                                       ##                    James McCormac                     ##                                                       ##########################################################To run this script type:

	cd /home/whtobs/acam/jmcc/under_development/domeflat/
	python domeflat.py camera num_flats_per_filt rspeed f1 f2 ... fn [DEBUG]
	
It will then take the flats in the normal order (not really important for dome 
flats). If a filter has not been observed with before the script will determine 
the best combination of lamps for efficient dome flats.  
Revision History:		v1.0	20/02/14	- Script started - JMCC
	For now I will comment out parts of autoflat not needed until after testing

	To do:
		test at WHT
		put the f_db and bias_db in the same place ans share them!
"""import sys, subprocess, signal, os, os.path, timefrom datetime import date, timedeltaprint("Modules loaded...")testdir = '~/Documents/ING/Scripts/ACAM/autoflat/test'#f_db='/home/whtobs/acam/jmcc/under_development/autoflat/FilterDB.txt'f_db='/Users/James/Documents/ING/Scripts/ACAM/autoflat/FilterDB.txt'bias_db='/home/whtobs/acam/jmcc/under_development/autoflat/BiasLevelDB.txt'
#domeflattime_db='/home/whtobs/acam/jmcc/under_development/autoflat/DomeFlatTimeDB.txt'
domeflattime_db='/Users/James/Documents/ING/Scripts/ACAM/autoflat/DomeFlatTimeDB.txt'camera_list=['acam']sat_count = 0# Functions #def CheckCommandLine():
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
	idle=""	counter = 0	while idle != "idling":		if camera_name == 'acam': 			idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]		#if camera_name == 'pfip':		#	do x y z				time.sleep(1)		counter += 1				if idle == "idling":			return 0				if counter == 30: # large enough?			co = raw_input("%s is not idle. Continue checking? [y/n]" % camera_name)			if co == 'n' or co == 'N' or co == 'q' or co == 'Q':				print("Exiting!!")				sys.exit(1)			counter = 0# Returns zero when the filter wheel is ready (only works for one filter being in place!)def WaitForFilterWheels(required_filter_serial_num):	"""
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
					co = raw_input("Waiting on the ACAM mirror. Continue checking? [y/n]")					if co == 'n' or co == 'N' or co == 'q' or co == 'Q':						print("Exiting!!")						sys.exit(1)					counter = 0def CheckTSSetup(camera_name):
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
	d=date.today()-timedelta(days=token)	# time of last data recorded?	x="%d%02d%02d" % (d.year,d.month,d.day)	if os.path.exists("/obsdata/whta/%s" % (x)) == True:	# looks for the data directory		data_loc="/obsdata/whta/%s" % (x)	elif os.path.exists("/obsdata/whtb/%s" % (x)) == True:		data_loc="/obsdata/whtb/%s" % (x)	else:		data_loc =0	return data_locdef SortFilters(token,f_list):
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
	print("Changing filter to %s..." % (name))	if camera_name == 'acam': # change for other cameras		os.system('acamimage %s' % name)		# check to see if the filter wheel is ready	ready = WaitForFilterWheels(serial_number)	if ready != 0:		print "Unexpected response while waiting for the filter wheels, aborting!"		os.system('abort %s &' % camera_name)	return 0def GetDomeFlatTime(filt,rspeed):
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

def SwitchOnLamps(lampcombo):
	
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
		
	return 0################################################################ Ctrl + C Trapping ###################################################################def signal_handler(signal, frame):
	"""
	A function to catch ctrl+c key presses and abort safely
	
	@rtype: int
	@return 0 = ok
	"""
		print('   Ctrl+C caught, shutting down...')	if DEBUG == 0:
		os.system('abort %s &' % camera_name)
		os.system('setccd %s domeflat' % camera_name)	sys.exit(0)signal.signal(signal.SIGINT, signal_handler)###################################################### Main ####################################################### make checks on all the numbers!
chkd,DEBUG,camera_name,filt_list=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()# summary lists
# a list for filter name, image number and median counts to print summary at the end
filt_summ, im_summ, med_summ = [],[],[]# Begin by making sure that the user is ready to take flatsprint("\nIt is assumed that the instrument, CCD, and windows are set up correctly.")
print("It is also assumed that the telescope is pointed at the dome flat position")
print("and the mirror petals are open. To QUIT and setup the instrument, type 'q'.")contin = raw_input("Press return to proceed.\n")if contin == 'n' or contin == 'N' or contin == 'q' or contin == 'Q':	print("Exiting!!")	sys.exit(0)# check the T/S is setup correctly for flats
print("Checking telescope is setup for %s..." % (camera_name))
if DEBUG == 0:
	setup = CheckTSSetup(camera_name)
	if setup != 0:
		print("Problem setting up the telescope for %s, exiting..." % (camera_name))
		sys.exit(0)# get afternoon or morning			token = GetAMorPM()# get tonights folderif DEBUG == 0:	data_loc=GetDataDir(token)	if data_loc==0:		print("Error finding data folder, exiting!")		sys.exit()if DEBUG == 1:
	data_loc=testdir	# get the list of filters	
n_filt=len(filt_list)# sort the filtersfilt_seq, serial_seq, bad_list = SortFilters(token,filt_list)# begin looping over required number of flats	for i in range(0,len(filt_seq)):		
	sat_count = 0 # reset the sat_count value for each filter
		# change to new filter	print("\nChanging filter to %s [%s]..." % (filt_seq[i],serial_seq[i]))
	if DEBUG == 0:
		c1=ChangeFilter(filt_seq[i], serial_seq[i])		if c1 != 0:			print("Problem changing filter, exiting!\n")			sys.exit()	
	
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
	if filt_seq[i] == filt_seq[-1]:			print ("No filters left, quiting!")
		print("Switching lamps off...")
		if DEBUG == 0:
			off=SwitchLampsOff()			
		break	
	