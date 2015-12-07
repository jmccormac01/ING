
#########################################################
#                                                       #
#               multdither.py ACAM v1.7                 #
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
#   v1.6   24/10/12 - Added WaitFor* functions to check noticeboard between TCS/ICS calls
#   v1.7   13/02/13 - Added check for guider stability so not to guide on trailed star
#	v1.8   15/06/13 - Added 31 position spiral pattern instead of the cross pattern
#

import sys, os
import time, signal

##################################################
############## Commandline Check #################
##################################################

if len(sys.argv) != 6:
	print "\nUSAGE: python multdither.py n_images exptime step_size on/off title"
	print "on/off is for autoguider on or off"
	print "e.g. python multdither.py 10 100 5 on QUSg\n"
	exit()

if sys.argv[4] != "on" and sys.argv[4] != "off":
	print "*Invalid autoguider value*, enter on/off"
	exit()

if sys.argv[4] == "on" and int(sys.argv[1]) > 30:
	print "*Cannot dither by more than 30 positions*\n*Run observations in smaller blocks*"
	exit()
	
if sys.argv[4] == "on" and int(sys.argv[1]) > 20:
	print "Do you really want more than 20 guided dither points (y/n)?"
	yn1=raw_input()
	if yn1 != "yes" and yn1 != "y":
		print "Exiting..."
		exit()
	z=raw_input("*CHECK WITH THE TO THAT GUIDING WON'T BE LOST*, THEN PRESS ENTER") 


##################################################
############ DEBUGGING MODE ON/OFF? ##############
##################################################

# 0 = off
# 1 = on	
DEBUG = 1

##################################################
############ Preset Spiral Pattern ###############
##################################################

spiralx=[0,1,1,0,-1,-1,-1, 0, 1, 2,2,2,2,1,0,-1,-2,-2,-2,-2,-2,-1, 0, 1, 2, 3, 3,3,3,3,3]
spiraly=[0,0,1,1, 1, 0,-1,-1,-1,-1,0,1,2,2,2, 2, 2, 1, 0,-1,-2,-2,-2,-2,-2,-2,-1,0,1,2,3]

for i in range(0,len(spiralx)):
	spiralx[i]=int(spiralx[i])*int(sys.argv[3])
	spiraly[i]=int(spiraly[i])*int(sys.argv[3])

# figure out if spiral pattern will be too big for guiding
sx=spiralx[:int(sys.argv[1])]
sy=spiraly[:int(sys.argv[1])]

print "\nRequested spiral size: "
print "\tX: %d'' --> %d''" % (min(sx), max(sx))
print "\tY: %d'' --> %d''" % (min(sy), max(sy))

if sys.argv[4] == "on":
	if min(sx) <= -30 or min(sy) <= -30 or max(sx) >= 30 or max(sy) >= 30:
		print "\nOuter sprial points will lose guiding!" 
		print "Please run smaller imaging blocks or step sizes"
		print "Min/Max dither positions = -20'' and +20''\n"
		exit()
	
	if min(sx) < -20 and min(sx) > -30 or min(sy) < -20 and min(sy) > -30 or max(sx) > 20 and max(sy) < 30 or max(sy) > 20 and max(sy) < 30:
		print "\n*MAKE SURE GUIDE STAR IS WELL CENTRED*"
		print "This observing block is close to the limits of dithered guiding!"
		print "Confirm with TO, continue? (y/n)"
		yn2=raw_input()
		if yn2 != "yes" and yn2 != "y":
			print "Exiting..."
			exit()

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal,frame):
	print '   Ctrl+C caught, shutting down...'
	if DEBUG == 0:
		os.system('abort acam &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##################################################
############# Wait for * functions ###############
##################################################

def WaitForIdle():
	
	idle=""
	
	while idle != "idling":
		idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.ACAM.CLOCKS_ACTIVITY').readline().split('\n')[0]
		time.sleep(1)
		
		if idle == "idling":
			return 0

def GetTeleStatus():
	
	stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
	
	return stat

def WaitForTracking():
	
	stat=""
	
	while stat != "TRACKING":
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		time.sleep(1)
		
		if stat == "TRACKING":
			return 0
			
def WaitForGuiding():
	
	stat=""
		
	while stat != "GUIDING":
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		
		# put this here so not to wait for 2 guide exposures if not necessary
		if stat == "GUIDING":
			return 0
	
		gsx=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDX').readline().split('\n')[0])
		gsy=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDY').readline().split('\n')[0])
	
		t_sleep=float(os.popen('ParameterNoticeBoardLister -i UDASCAMERA.AUTOCASS.T_DEMAND').readline().split('\n')[0])
		time.sleep(t_sleep+3)
		
		gsx_n=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDX').readline().split('\n')[0])
		gsy_n=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDY').readline().split('\n')[0])
		
		# check that the guide star positions are not the same
		# i.e. if using long guide exposures
		if gsx_n != gsx and gsy_n != gsy:
			if abs(gsx_n-gsx) < 10 and abs(gsy_n-gsy) < 10:
				os.system('tcsuser "autoguide on"')
				time.sleep(2)
		

##################################################
############## Autoguiding ON/OFF? ###############
##################################################

if sys.argv[4] == "on":
	
	print "Switching on the guider..."
	if DEBUG == 0:
		stat=GetTeleStatus()
		if stat != "GUIDING":
			yn=raw_input("\nTELESCOPE NOT GUIDING, START AUTOGUIDER, THEN PRESS ENTER\n")
			done=WaitForGuiding()
	
	
if sys.argv[4] == "off":
	
	print "Checking telescope is tracking..."
	if DEBUG == 0:
		stat=GetTeleStatus()
		if stat != "TRACKING":
			if stat == "GUIDING":
				print "\nTELESCOPE IS GUIDING, STOPPING GUIDER...\n"
				os.system('tcsuser "autoguide off"')
				done=WaitForTracking()
			
			if stat == "MOVING":
				print "\nTELESCOPE IS MOVING, WAITING...\n"
				done=WaitForTracking()
				


##################################################
###################### Main ######################
##################################################
	
# set +3s delay to demanded exposure time for starting offsets
st=int(sys.argv[2])+3

# set image number counters
i=1
k=0

# take first image undithered
print "Offset [1]: 0 0"
print "Image [1]"
if DEBUG == 0:
	os.system('run acam %d "%s 0 0" &' % (int(sys.argv[2]),sys.argv[5]))

time.sleep(st)

# start loop over number of images required - 1
while i < int(sys.argv[1]):
		
	x=int(spiralx[i])
	y=int(spiraly[i])
	i=i+1
	
	# check the image number just in case
	if i > int(sys.argv[1]):
		break
			
	# check if guiding is used and turn it off for dithering if needed
	if sys.argv[4] == "on":
		print "Autoguider OFF"
		if DEBUG == 0:
			os.system('tcsuser "autoguide off"')
			done=WaitForTracking()
	
	print "Offset [%d]: %d %d..." % (i, x, y)
	if DEBUG == 0:
		os.system('offset arc %d %d' % (x,y))
		done=WaitForTracking()
			
	# resumme guiding if necessary
	if sys.argv[4] == "on":
		print "Autoguider ON..."
		if DEBUG == 0:
			done=WaitForGuiding()
	
	# wait for CCD clocks to be IDLE
	print "Waiting for CCD to idle..."	
	if DEBUG == 0:
		 
					
	# take the next ACAM image
	print "Image [%d]" % (i)
	if DEBUG == 0:
		os.system('run acam %d "%s %d %d" &' % (int(sys.argv[2]),sys.argv[5], x, y))
	time.sleep(st)		
					

# return the telescope to the original position
if sys.argv[4] == "on":
	print "Switching off guider..."
	if DEBUG == 0:
		os.system('tcsuser "autoguide off"')
		done=WaitForTracking()

print "Returning telescope to 0 0..."
if DEBUG == 0:
	os.system('offset arc 0 0')
	done=WaitForTracking()

if sys.argv[4] == "on":
	print "Switching guiding back on..."
	if DEBUG == 0:
		done=WaitForGuiding()

