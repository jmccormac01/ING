

#########################################################
#                                                       #
#           multdither_pfip.py PFIP v1.0                #
#                                                       #
#                   James McCormac                      #
#                                                       #
#########################################################
#
#	Revision History:	
#   v1.0   12/11/12 - Script written
#                   - Script tested on sky, works well - check guider continously
#

import os, time, signal, sys

##################################################
############# Wait for * functions ###############
##################################################

def WaitForIdle():
	
	idle=""
	
	while idle != "idling":
		idle=os.popen('ParameterNoticeBoardLister -i UDASCAMERA.PFIP.CLOCKS_ACTIVITY').readline().split('\n')[0]
		time.sleep(1)
		
		if idle == "idling":
			return 0
			
			
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
		gsx=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDX').readline().split('\n')[0])
		gsy=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDY').readline().split('\n')[0])
		
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		time.sleep(5)
		
		gsx_n=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDX').readline().split('\n')[0])
		gsy_n=float(os.popen('ParameterNoticeBoardLister -i AG.GUIDESTAR.CENTROIDY').readline().split('\n')[0])
		
		if abs(gsx_n-gsx) < 10 and abs(gsy_n-gsy) < 10:
			os.system('tcsuser "autoguide on"')
		
		if stat == "GUIDING":
			return 0

def GoTo(tar):
	
	comm="gocat %s &" % (tar)
	os.system(comm)	

	return 0


def MoveProbe(x,y):
	
	comm="agprobe %s %s" % (x, y)
	os.system(comm)
	
	return 0

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print '   Ctrl+C caught, shutting down...'
	os.system('abort pfip &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


##################################################
############## Commandline Check #################
##################################################

if len(sys.argv) != 2:
	print "\nUSAGE: python multdither_pfip.py file"
	print "e.g. python multdither_pfip.py PA1\n"
	exit()

##################################################
#################### FIELDS ######################
##################################################

# targets - get fields from a file
# get guide probe possitons for the field from file
f=open('%s.txt' % (sys.argv[1])).readlines()

name,x,y=[],[],[]

for i in range(0,len(f)):
	name.append(f[i].split()[0])
	x.append(f[i].split()[7])
	y.append(f[i].split()[8])
	
##################################################
###################### Main ######################
##################################################

texp=120
st=texp+3

for j in range(0,len(name)):
	
	os.system('tcsuser "autoguide off"')
	
	# move to target
	print "Moving to %s..." % (name[j])
	go=GoTo(name[j])
	
	# move guide probe
	print "Moving probe to %s %s..." % (x[j],y[j])
	probe=MoveProbe(x[j],y[j])
	
	# wait for telescope tracking
	print "Waiting for the telescope to start tracking..."
	track=WaitForTracking()
	
	# sleep for 2s after tracking starts - can be removed after testing 
	time.sleep(2)
		
	# wait for guiding
	print "Waiting for the autoguider..."
	guide=WaitForGuiding()
	
	# sleep for 2s after guiding stars - can be removed after testing
	time.sleep(2)
	
	# wait for CCD to be ready
	print "Waiting for the CCD to idle..."
	idle=WaitForIdle()
	
	# call image
	print "Imaging %d s at target %s..." % (texp,name[j])
	os.system('run pfip %d "%s" &' % (texp,name[j]))
	
	# sleep for exptime+3s before startin next loop
	time.sleep(st)

	
	