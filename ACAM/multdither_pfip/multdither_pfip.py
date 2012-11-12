

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
#

import os, time

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
		stat=os.popen('ParameterNoticeBoardLister -i TCS.telstat').readline().split('\n')[0]
		time.sleep(1)
		
		if stat == "GUIDING":
			return 0

def GoTo(tar):
	
	comm="gocat %s" % (tar)
	os.system(comm)	

	return 0


def MoveProbe(x,y):
	
	comm="agprobe %s %s" % (x, y)
	os.system(comm)
	
	return 0


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
	x.append(f[1].split()[7])
	y.append(f[1].split()[8])
	
##################################################
###################### Main ######################
##################################################

texp=180
st=texp+3

for j in range(0,len(name)):
	
	# move to target
	go=GoTo(name[j])
	
	# move guide probe
	probe=MoveProbe(x[j],y[j])
	
	# wait for telescope tracking
	track=WaitForTracking()
	
	# sleep for 2s after tracking starts - can be removed after testing 
	time.sleep(2)
	
	# turn on guider - hopefully this will help probe movement ambiguity
	# if not just add fixed sleep time
	os.system('tcsuser "autoguide on"')
	
	# wait for guiding
	guide=WaitForGuiding()
	
	# sleep for 2s after guiding stars - can be removed after testing
	time.sleep(2)
	
	# wait for CCD to be ready
	idle=WaitForIdle()
	
	# call image
	os.system('run pfip %d "%s" &' % (texp,name[j]))
	
	# sleep for exptime+3s before startin next loop
	time.sleep(st)
	
	