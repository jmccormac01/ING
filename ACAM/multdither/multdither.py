
#########################################################
#                                                       #
#               multdither.py ACAM v1.5                 #
#                                                       #
#           IF AUTOGUIDING PLEASE ENSURE                #
#        GUIDING IS ON BEFORE RUNNING SCRIPT!           #
#                                                       #
#                   James McCormac                      #
#                                                       #
#########################################################
#
#	Revision History:	
#   v1.0   10/04/12 - Script written
#   v1.1   20/07/12 - Script tested 
#                   - Added auto-on/off capability
#   v1.2   13/08/12 - Corrected offset arc 0 0 error at end if guiding
#   v1.3   03/09/12 - Added title and offsets to object name
#   v1.4   12/09/12 - Added get_acam_params at beginning 
#                     to calculate dead time between exposures
#          27/09/12 - Added DEBUG mode for testing script skeleton only		
#                   - Added CTRL+C trapping
#   v1.5   04/09/12 - Removed dt calcs and added watch to CCD clocks for idle
#                     Tested at telescope and works perfectly

import sys, os
import time, signal

##################################################
############## Commandline Check #################
##################################################

if len(sys.argv) != 6:
	print "\nUSAGE: python multdither.py num exptime step auto-on/off title"
	print "e.g. python multdither.py 10 100 5 on QUSg\n"
	exit()

if sys.argv[4] != "on" and sys.argv[4] != "off":
	print "Invalid autoguider value, enter on/off"
	exit()
	
if sys.argv[4] == "on" and int(sys.argv[1]) > 10:
	print "Do you really want more than 10 guided dither points (y/n)?"
	yn1=raw_input()
	if yn1 != "yes" and yn1 != "y":
		exit()
	z=raw_input("CHECK WITH TO GUIDING WON'T BE LOST, THE PRESS ENTER") 


##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print '   Ctrl+C caught, shutting down...'
	os.system('abort acam &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##################################################
############ Wait for IDLE function ##############
##################################################

def WaitForIdle():
	
	idle=""
	
	while idle != "idling":
		idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]
		time.sleep(1)
		
		if idle == "idling":
			return 0
	
# 0 = off
# 1 = on	
DEBUG = 0

##################################################
############## Autoguiding ON/OFF? ###############
##################################################

# set guide sleep time - time to sleep after turning guiding back on
if sys.argv[4] == "on":
	gst=10
	yn=raw_input("\nCHECK WITH TO THAT AUTOGUIDING IS *ON*, THEN PRESS ENTER\n")

if sys.argv[4] == "off":
	gst=0
	yn=raw_input("\nCHECK WITH TO THAT AUTOGUIDING IS *OFF*, THEN PRESS ENTER\n")	


##################################################
###################### Main ######################
##################################################
	
# set +3s delay to demanded exposure time for starting offsets
st=int(sys.argv[2])+3

# set offset sleep time - time to sleep after applying telescope offset
ost=10

# set image number counters
i=1
k=0

# take first image undithered
print "Offset [1]: 0 0"
if DEBUG == 0:
	print "Image [1]"
	os.system('run acam %d "%s 0 0" &' % (int(sys.argv[2]),sys.argv[5]))

time.sleep(st)

# start loop over number of images required - 1
while i < int(sys.argv[1]):
	
	# increase step size accordingly
	t=int(sys.argv[3])+(int(sys.argv[3])*k)
		
	# cycle through box pattern of ++, --, +-, -+
	for j in range(0,4):
	
		if j == 0:
			xs=1
			ys=1
			
		if j == 1:
			xs=-1
			ys=-1
			
		if j == 2:
			xs=-1
			ys=1
			
		if j == 3:
			xs=1
			ys=-1
		
		x=t*xs
		y=t*ys
		i=i+1
		
		if i > int(sys.argv[1]):
			break
				
		# check if guiding is used and turn it off for dithering if needed
		if sys.argv[4] == "on":
			print "Autoguider OFF"
			if DEBUG == 0:
				os.system('tcsuser "autoguide off"')
		
		print "Offset [%d]: %d %d, sleeping for %d s..." % (i, x, y, ost)
		os.system('offset arc %d %d' % (x,y))
		time.sleep(ost)
				
		# resumme guiding if necessary
		# check dead time and include any additional sleep required here
		# so the next run call does not clash with previous readout
		if sys.argv[4] == "on":
			if DEBUG == 0:
				os.system('tcsuser "autoguide on"')
								
			print "Autoguider ON, sleeping for %d s..." % (gst)
			time.sleep(gst)
			
		idle=WaitForIdle()
		if idle != 0:
			print "Unexpected response while waiting for CCD to idle, aborting!"
			os.system('abort acam &')
			exit()
						
		# take the next ACAM image
		if DEBUG == 0:
			print "Image [%d]" % (i)
			os.system('run acam %d "%s %d %d" &' % (int(sys.argv[2]),sys.argv[5], x, y))
			time.sleep(st)		
					
	k=k+1

# return the telescope to the original position
if sys.argv[4] == "on":
	if DEBUG == 0:
		os.system('tcsuser "autoguide off"')
		time.sleep(gst)

if DEBUG == 0:
	os.system('offset arc 0 0')

if sys.argv[4] == "on":
	time.sleep(gst)
	if DEBUG == 0:
		os.system('tcsuser "autoguide on"')

