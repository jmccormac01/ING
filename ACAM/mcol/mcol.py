#########################################################
#                                                       #
#                  mcol.py ACAM v1.0                    #
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
#	

import sys, os
import signal

##################################################
############## Commandline Check #################
##################################################

# check command line args are present
if len(sys.argv) < 4:
	print '\nUSAGE: python mcol.py name on/off "F1,N1,E1,on/off" ... "Fn,Nn,En,on/off"'
	print '\nwhere:'
	print '\tname: target name'
	print '\ton/off: dithering on/off'
	print '\t"F1,N1,E1,on/off": filt1, num_exps1, exp_time1, a/g on/off'
	print '\n\t*NOTE quoation marks are required around each observing block*\n'
	print 'e.g. python mcol.py QUSge on "V,10,300,on" "B,5,100,off"\n'
	exit()

if sys.argv[2] != "on" and sys.argv[2] != "off":
	print "Invalid dither on/off selection"
	print "Please enter on or off"
	print "Check there are no spaces in the target name"


# split args
filt,num,exptime,ag=[],[],[],[]

for i in sys.argv[3:]:
	filt.append(i.split(',')[0])
	num.append(i.split(',')[1])
	exptime.append(i.split(',')[2])
	ag.append(i.split(',')[3])

# check filters against filter database (to be made)

# check number of observations when dithering and autoguiding
if sys.argv[2] == "on":
	for i in range(0,len(ag)):
		if ag[i] == "on" and int(num[i]) > 10:
			yn=raw_input("\nAre you sure you want more than 10 dithered guided exposures? (y/n): ")
			if yn != "yes" and yn != "y":
				exit()
			if yn == "yes" or yn == "y":
				yn2=raw_input("\nCheck with TO that autoguiding will not be lost, the press ENTER\n")	


# put any unguided runs last so the guiding doesn't drift between runs 	
if "off" in ag:
	print "Placing unguided observations at the end of the run"
	temp=zip(ag,filt,num,exptime)
	temp.sort(reverse=True)
	ag,filt,num,exptime=zip(*temp)
	
	
##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print '   Ctrl+C caught, shutting down...'
	os.system('abort acam &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##################################################
###################### Main ######################
##################################################













