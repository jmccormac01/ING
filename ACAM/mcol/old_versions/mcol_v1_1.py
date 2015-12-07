#########################################################
#                                                       #
#                  mcol.py ACAM v1.1                    #
#                                                       #
#        An observing block script to do coloured       #
#        observations, with or without guiding &        #
#                      dithering                        #
#                                                       #
#                    James McCormac                     #
#                                                       #
#########################################################
#
#	Revision History:	
#   v1.0   03/10/12 - Script written
#   v1.1   24/10/12 - Script Tested
#                   - Added ParameterNoticeBoard checking for Tele and CCD  
#

import sys, os
import signal
import time

def printUsage(xit):
	print '\nUSAGE: python mcol.py name on/off [step] "F1,N1,E1,on/off" ... "Fn,Nn,En,on/off"'
	print '\nwhere:'
	print '\tname: target name'
	print '\ton/off: dithering on/off'
	print '\tif dithering on, give step size in arcsec'
	print '\t"F1,N1,E1,on/off": filt1, num_exps1, exp_time1, a/g on/off'
	print '\n\t*NOTE quoation marks are required around each observing block*\n'
	print 'e.g. python mcol.py QUSge on 5 "V,10,300,on" "B,5,100,off"\n'
	
	if xit==1:
		exit()

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
		time.sleep(1)
		
		if stat == "GUIDING":
			return 0	

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print '   Ctrl+C caught, shutting down...'
	os.system('abort acam &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##################################################
############## Commandline Check #################
##################################################

# check command line args are present
if len(sys.argv) < 4:
	printUsage(1)

if sys.argv[2] == "on" and len(sys.argv) < 5:
	printUsage(1)
	
if sys.argv[2] == "off" and len(sys.argv) < 4:
	printUsage(1)

if sys.argv[2] != "on" and sys.argv[2] != "off":
	print "Invalid dither on/off selection"
	print "Please enter on or off"
	print "Check there is a target name with no spaces"
	exit()


# split args
filt,num,exptime,ag=[],[],[],[]

if sys.argv[2] == "off":
	fs=3
if sys.argv[2] == "on":
	fs=4

# invalid observing block counter
inv=0

for i in sys.argv[fs:]:

	if len(i.split(',')) == 4:
		filt.append(i.split(',')[0])
		num.append(i.split(',')[1])
		exptime.append(i.split(',')[2])
		ag.append(i.split(',')[3])

	if len(i.split(',')) != 4:
		print '\n***Invalid observing sequence block "%s"***' % (i)
		print '***See USAGE below and try again***'
		inv=inv+1
	
if inv >= 1:
	printUsage(1)
	
# print observing block summary
for i in range(0,len(filt)):
	print "Block %d:" % (i)
	print "\tFilter: %s, Number: %s, ExpTime: %s s, Autoguider: %s" % (filt[i], num[i], exptime[i], ag[i])
		
# check filters against filter database (to be made)

# check number of observations when dithering and autoguiding
if sys.argv[2] == "on":
	for i in range(0,len(ag)):
		if ag[i] == "on" and int(num[i]) > 10 and sys.argv[3] >= 5:
			yn=raw_input("\nAre you sure you want more than 10 dithered guided exposures? (y/n): ")
			if yn != "yes" and yn != "y":
				exit()
			if yn == "yes" or yn == "y":
				yn2=raw_input("\nCheck with TO that autoguiding will not be lost, the press ENTER\n")	


# put any unguided runs last so the guiding doesn't drift between runs 	
if "off" in ag and "on" in ag:
	print "Placing unguided observations at the end of the run"
	temp=zip(ag,filt,num,exptime)
	temp.sort(reverse=True)
	ag,filt,num,exptime=zip(*temp)

if "on" in ag:
	stat=GetTeleStatus()
	if stat != "GUIDING":
		yn=raw_input("\nTELESCOPE NOT GUIDING, START AUTOGUIDER, THEN PRESS ENTER\n")
		done=WaitForGuiding()


##################################################
###################### Main ######################
##################################################

for i in range(0,len(filt)):
	
	print "Changing filter to %s" % (filt[i])
	os.system("acamimage %s" % filt[i])
	
	# no dithering
	if sys.argv[2] == "off":
		
		if ag[i] == "off":
			stat=GetTeleStatus()
			if stat== "GUIDING":
				print "Switching off autoguider..."
				os.system('tcsuser "autoguide off"')
				done=WaitForTracking()
		
		# wait for CCD clocks to be IDLE	
		idle=WaitForIdle()
		
		print "Calling multrun acam with %s %s %s_%s" % (num[i],exptime[i],sys.argv[1],filt[i])
		os.system('multrun acam %s %s "%s_%s"' % (num[i],exptime[i],sys.argv[1],filt[i]))
		
	# dithering
	if sys.argv[2] == "on":
		
		# wait for CCD clocks to be IDLE	
		idle=WaitForIdle()
		
		print "Calling multdither with %s %s %s %s %s_%s" % (num[i],exptime[i],sys.argv[3],ag[i],sys.argv[1],filt[i])
		os.system('python /home/whtobs/acam/jmcc/multdither.py %s %s %s %s %s_%s' % (num[i],exptime[i],sys.argv[3],ag[i],sys.argv[1],filt[i]))








