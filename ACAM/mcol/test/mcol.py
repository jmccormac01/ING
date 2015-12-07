#########################################################
#                                                       #
#                  mcol.py ACAM v2.0                    #
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
#   v2.0   24/11/13 - Added check if need quit
#                     Added TEST and DEBUG like multdither
#                     Added more checks on the command line args
#                     Added OBSSYS to look for the right multdither in ICS 
#          03/01/14 - made this test version in stable until the ICS release.

# to do: check filter database
#		 log the outputs
#        add verbose option?
#

import sys, os
import time, signal, string, select
import commands as cmd

##################################################
######### CHANGE BEFORE TESTING ON ICS ###########
##################################################

testscript = '/home/whtobs/acam/jmcc/stable'
#testscript = '~/Documents/ING/Scripts/ACAM/mcol/test'

##################################################
############## OBSSYS DEFINITION #################
##################################################

# get the current observing system location
obssys=cmd.getoutput('echo $OBSSYS')
if len(obssys) < 1:
	obssys = testscript

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print '   Ctrl+C caught, shutting down...'
	if DEBUG == 0:
		os.system('abort acam &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# second abort method
def check_if_need_to_quit():
	x,a,b=select.select([sys.stdin], [], [], 0.001)
	if (x):
		char=sys.stdin.readline().strip()
		if char[0] == 'q':
			q=string.lower(raw_input('Are you sure you want to quit (y/n)? '))
			while (q[0] != 'y') and (q[0] != 'n'):
				q=string.lower(raw_input())
			if q[0] == 'y':
				print("exiting")
				os.system('abort acam &')
				return 1
	return 0

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


def printUsage():
	print '\nUSAGE: mcol acam "name" on/off [step] "F1,N1,E1,auto_on/off" ... "Fn,Nn,En,on/off" [TEST  DEBUG]'
	print '\nwhere:'
	print '\tacam: instrument name (ACAM only for now)'
	print '\tname: target name in quotes'
	print '\ton/off: dithering on/off'
	print '\tif dithering on, give step size in arcsec'
	print '\t"F1,N1,E1,on/off": filt1, num_exps1, exp_time1, auto_on/off'
	print '\t*NOTE quotation marks are required around each observing block*'
	print '\tTEST: to run development scripts (not advised)'
	print '\tDEBUG: to simulate image capture & filter changes (not advised)\n'
	print 'e.g. mcol acam "QUSge" on 5 "V,10,300,auto_on" "B,5,100,auto_off"\n'
				

def CheckCommandLine():
	
	# check command line args are present
	if len(sys.argv) < 4:
		printUsage()
		exit()
	
	returnval = 0
	
	# function to check command line args [1], [2] and [3] are valid
	# check image name is not test or debug
	if sys.argv[1] == 'debug' or sys.argv[1] == 'DEBUG' or sys.argv[1] == 'test' or sys.argv[1] == 'TEST':
		print "\nImage name INVALID! Cannot use 'debug' or 'test'"
		returnval = returnval + 1
	else:
		print "\nImage name is valid..."
	
	# check dithering command is on or off only
	if sys.argv[2] != "on" and sys.argv[2] != "off":
		print "Dithering request is INVALID! Enter on or off"
		returnval = returnval + 1 
	else:
		print "Dithering request is valid..."
	
	# if dithering is on check step size is an integer
	if sys.argv[2] == "on":
		try:
			float(sys.argv[3])
		except ValueError:
			print "Dithering step size is INVALID!"
			returnval = returnval + 1	 
		else:
			print "Step size is valid..."		
				
	return returnval


def GetBlockList():
	# check for test and debug
	fe=0

	if 'DEBUG' in sys.argv or 'debug' in sys.argv:
		DEBUG = 1
		print "\n*************************************************"
		print "************ ENTERING DEBUGGING MODE ************"
		print "*** NO IMAGES WILL BE TAKEN. SIMULATION ONLY! ***"
		print "*************************************************\n"
		fe = fe -1
	else:	
		DEBUG = 0
	
	if 'TEST' in sys.argv or 'test' in sys.argv:
		TEST = 1
		print "\n*************************************************"
		print "************** RUNNING TEST MODE! ***************"
		print "*************************************************\n"
		fe = fe -1
		
		print "Running test script in: "
		print "%s" % (testscript)
		
		l=len(sys.argv) - 2
		comm=sys.argv[1]
		for i in range(2,l):
			comm=comm+" %s" %(sys.argv[i])
		
		if DEBUG == 1:				
			comm=comm+" debug"
		
		os.system('python %s/mcol.py %s' % (testscript, comm))

		exit()
		
	else:
		TEST = 0
	
	
	# get the observing blocklist
	if sys.argv[2] == "off":
		if fe == 0:
			blocklist = sys.argv[3:]
		else:
			blocklist = sys.argv[3:fe]
	if sys.argv[2] == "on":
		if fe == 0:
			blocklist = sys.argv[4:]
		else:
			blocklist = sys.argv[4:fe]

	return TEST, DEBUG, blocklist


def CheckBlocks(blocklist):

	# lists for block elements
	filt,num,exptime,ag=[],[],[],[]
	
	# invalid observing block counter
	inv=0
	
	print "Checking observing blocks...\n"
	
	for i in blocklist:
		if len(i.split(',')) == 4:
			filt.append(i.split(',')[0])
			num.append(i.split(',')[1])
			exptime.append(i.split(',')[2])
			ag.append(i.split(',')[3])
	
		if len(i.split(',')) != 4:
			print '\nObserving sequence block "%s" is INVALID!' % (i)
			inv=inv+1
	
	# check filters against filter database (to be made)
	
	# check image numbers, exposure times and auto_on/off
	for i in range(0,len(num)):
		try:
			int(num[i])
		except ValueError:
			print "Image number %d is INVALID!" % (i+1)
			inv = inv + 1		 
		else:
			print "Image number %d is valid..." % (i+1)
	
		try:
			float(exptime[i])
		except ValueError:
			print "Exposure time %d is INVALID!" % (i+1)
			inv = inv + 1		 
		else:
			print "Exposure time %d is valid..." % (i+1)
	
		if ag[i] != "auto_on" and ag[i] != "auto_off":
			print "Autoguider request %d INVALID!" % (i+1)
			inv = inv + 1
		else:
			print "Autoguider request %d valid..." % (i+1)
		print "\n"
			
	return inv,filt,num,exptime,ag
		

##################################################
############## Commandline Check #################
##################################################


# make checks on the intial command line args
chkd=CheckCommandLine()
if chkd != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	exit()
	
# check for test and debug and get the blocklist
TEST,DEBUG,blocklist=GetBlockList()

# check the blocklist is ok
inv,filt,num,exptime,ag=CheckBlocks(blocklist)
if inv != 0:
	print "Problems detected on command line, try again. Exiting...\n"
	printUsage()
	exit()

# how to abort	
print "To ABORT this script: "
print "1) Press ctrl+c at anytime - or -"
print "2) type 'q' and press ENTER"
print "The script should stop and abort ACAM imaging shortly after.\n"
#raw_input('Press ENTER to continue...')	

# check number of observations when dithering and autoguiding
if sys.argv[2] == "on":
	for i in range(0,len(ag)):
		if ag[i] == "auto_on" and int(num[i]) > 10 and sys.argv[3] >= 5:
			yn=raw_input("\nAre you sure you want more than 10 dithered guided exposures? (y/n): ")
			if yn != "yes" and yn != "y":
				exit()
			if yn == "yes" or yn == "y":
				yn2=raw_input("\nCheck with TO that autoguiding will not be lost, the press ENTER\n")	


# put any unguided runs last so the guiding doesn't drift between runs 	
if "auto_off" in ag and "auto_on" in ag:
	print "Placing unguided observations at the end of the run"
	temp=zip(ag,filt,num,exptime)
	temp.sort(reverse=True)
	ag,filt,num,exptime=zip(*temp)

# print observing block summary
for i in range(0,len(filt)):
	print "Block %d:" % (i+1)
	print "\tFilter: %s, Number: %s, ExpTime: %s s, Autoguider: %s" % (filt[i], num[i], exptime[i], ag[i])
print "\n"

if "auto_on" in ag:
	if DEBUG == 0:
		stat=GetTeleStatus()
		if stat != "GUIDING":
			yn=raw_input("\nTELESCOPE NOT GUIDING, START AUTOGUIDER, THEN PRESS ENTER\n")
			done=WaitForGuiding()


##################################################
###################### Main ######################
##################################################

for i in range(0,len(filt)):
	
	print "Changing filter to %s" % (filt[i])
	if DEBUG == 0:
		os.system("acamimage %s" % filt[i])
	
	# no dithering
	if sys.argv[2] == "off":
		print "Checking telescope is tracking..."
		if DEBUG == 0:
			if ag[i] == "auto_off":
				stat=GetTeleStatus()
				if stat== "GUIDING":
					print "Switching off autoguider..."
					os.system('tcsuser "autoguide off"')
					done=WaitForTracking()
				
				if stat == "MOVING":
					print "\nTELESCOPE IS MOVING, WAITING...\n"
					done=WaitForTracking()
				
		# wait for CCD clocks to be IDLE	
		print "Checking CCD clocks are idle..."
		if DEBUG == 0:
			idle=WaitForIdle()
		
		print "Calling multrun acam with %s %s %s_%s" % (num[i],exptime[i],sys.argv[1],filt[i])
		if DEBUG == 0:
			os.system('multrun acam %s %s "%s_%s"' % (num[i],exptime[i],sys.argv[1],filt[i]))
	
	
		
	# dithering
	if sys.argv[2] == "on":
		
		# wait for CCD clocks to be IDLE	
		print "Checking CCD clocks are idle..."
		if DEBUG == 0:
			idle=WaitForIdle()
		
		print "Calling multdither with %s %s %s %s %s_%s" % (num[i],exptime[i],sys.argv[3],ag[i],sys.argv[1],filt[i])
		if DEBUG == 0:
			if TEST == 0:
				os.system('python /home/whtobs/acam/jmcc/stable/multdither.py %s %s %s %s %s_%s' % (num[i],exptime[i],sys.argv[3],ag[i],sys.argv[1],filt[i]))

			
	if check_if_need_to_quit():
		break	



