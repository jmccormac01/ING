#########################################################
#						Fixed some coding errors with the save/setccd calls, to be tested
#						on sky - JMCC						
#   continue testing on sky
#   add 10s-->2s if 10s saturated on previous filter in morning.
# 

num_flats_tot=(len(sys.argv)-4)*int(sys.argv[2])

	contin = raw_input("Are you sure you want to continue? [y/n]")
	idle=""
	while idle != "idling":
		if camera_name == 'acam': 
			idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]
		#if camera_name == 'pfip':
		#	do x y z
		
		time.sleep(1)
		
		if idle == "idling":
			return 0
		if counter == 30: # large enough?
	stat=""
	while stat != "TRACKING":
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		
		time.sleep(1)
		if stat == "TRACKING":
		if counter == 30:
	counter = 0
			time.sleep(1)
				counter = 0
	if lday != day or lmonth != month or lyear != year:	# if there is no bias level in the database,
		
		print('No bias levels in database, taking bias images to check...')
		
		# fast
		
		print("[Ftest] Sky Level: %d Required Exptime: %.2f" % (int(sky_lvl),req_exp))
	print("It is assumed that the instrument, CCD, and windows are set up for the observation.")
					# now use setccd here to return the CCD to previous state
					print("Reseting CCD to observing mode")
					os.system('setccd %s autoflat' % camera_name)
		
				#print("Setting rspeed back to %s..." % (sys.argv[3]))
				
				# restore the ccd to it's original settings so that the flats match the observations
				os.system('setccd %s autoflat' % camera_name)
				
					os.system('setccd %s autoflat' % camera_name)
					
					#if camera_name == 'acam':
				# restore the ccd to it's original settings so that the flats match the observations
				os.system('setccd %s autoflat' % camera_name)
		