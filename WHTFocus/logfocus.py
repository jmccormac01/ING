
#########################################################
#                                                       #
#                  	 logfocus.py v2.0                   #
#                                                       #
#                     James McCormac                    #
#                                                       #
#########################################################
#
#   A script to log the WHT Instruments focus values
#
#   Revision History:	
#   v1.0	08/04/14 -	script writen (JMCC)
#	v1.1	10/04/14 -	added stuff for logging ELEVATION
#						seems we need to manually log TC and DF
#						after chat with Sergio. Changes made.
# 						Added check to instrument name
#	v1.2	22/04/14 -	Added automatic TC - tested working fine
#	v1.3	08/04/14 -	Changed TC,DF,AC to commands from ICS, easier.
#	v2.0	13/05/14 - 	Added in INT support
#
#   To do:
#		- Write a plotting script to plot the values between
#		  dates X and Y
#		- Add final error checking
#	   
# *** NEEDS TESTED AGAIN IN WHT AND INT ***
#

import argparse as ap
import numpy as np
import MySQLdb
import sys, os

#######################
###### FUNCTIONS ######
#######################

# argparse assumes type=string unless told otherwise
def ArgParse():
	
	parser=ap.ArgumentParser()
	parser.add_argument("instrument", help="name of instrument which has been focused e.g. acam")
	parser.add_argument("focus", help="focus value in mm. e.g. 98.00")
	args=parser.parse_args()
		
	return args

# get the elevation of the t/s
def GetElevation():

	el=os.popen('ParameterNoticeBoardLister -i TCS.alt').readline().split('\n')[0]	
	
	try:
		el="%.2f" % (np.degrees(float(el)))
	except ValueError:
		print "Error getting telescope elevation"
		print "Is ParameterNoticeBoard online, if not submit Fault Report"
		print "Setting elevation to 90 degs"
		el = "90.00"
	
	return el

# get the temperature compensation, altitude compensation and telescope defocus
def GetData():
	
	tc=os.popen('cmd -g TCS POSITION.focTmpCorr').readlines()[1].split()[-1]
	ac=os.popen('cmd -g TCS POSITION.focAltCorr').readlines()[1].split()[-1]
	df=os.popen('cmd -g TCS POSITION.focFltCorr').readlines()[1].split()[-1]
	
	try:
		tc="%.2f" % (float(tc))
	except ValueError:
		print "Error getting temperature compensation value"
		print "Is DRAMA online, if not try restarting DRAMA to enable automatic logging of TCS parameters"
		print "Setting TempComp to 0 mm/K" 
		tc="0.00"
	
	try:
		ac="%.2f" % (float(ac))
	except ValueError:
		print "Error getting altitude compensation value"
		print "Is DRAMA online, if not try restarting DRAMA to enable automatic logging of TCS parameters"
		print "Setting AltComp to 0 mm/deg" 
		ac="0.00"
	
	try:
		df="%.2f" % (float(df))
	except ValueError:
		print "Error getting telescope defocus value"
		print "Is DRAMA online, if not try restarting DRAMA to enable automatic logging of TCS parameters"
		print "Setting DF to 0 mm" 
		df="0.00"
	
	return tc,ac,df

######################
######## MAIN ########
######################

# parse command line arguments
args=ArgParse()

# list of available instruments
# check the one entered it correct
inst_list=['ACAM','AF2','CANARY','EXPO','GHAFAS','IDS','INTEGRAL','INGRID','ISIS','LIRIS','NAOMI','PFIP','PLANETPOL','PNS','SAURON','ULTRACAM','WFC']

if args.instrument.upper() not in inst_list:
	print "\n\t%s not in instrument list. Check spelling?" % (args.instrument.upper())
	print "\tInstrument List: "
	print "\t" + str(inst_list[0:5])[1:-1]
	print "\t" + str(inst_list[5:10])[1:-1]
	print "\t" + str(inst_list[10:-1])[1:-1]
	print "\tExiting...\n"
	sys.exit()

if args.instrument.upper() == 'IDS' or args.instrument.upper() == 'WFC':
	telescope = 'INT'
else:
	telescope = 'WHT'

# add a check for strange focus values
# make an array with typical values and then allow +/- 5mm on that?

# get the date today
from datetime import datetime
t=datetime.today().isoformat()[:10]

# connect to focus database
db=MySQLdb.connect(host='dbstore.ing.iac.es',user='jmcc',passwd='!jmcc!', db='focus')

# get database cursor
cur=db.cursor()

fields=['date','instrument','focus','tc','df','ac','el']
vals=[]

# get EL and TC
el=GetElevation()
tc,ac,df=GetData()

# make list for logging to database
vals.append(t)
vals.append(args.instrument.upper())
vals.append(args.focus)
vals.append(tc)
vals.append(df)
vals.append(ac)
vals.append(el)

# make the list a tuple
vals_n=tuple(vals)

# log to the database
try:
	if telescope == 'WHT':
		cur.execute('''INSERT INTO wht_focus (date,instrument,focus,tc,df,ac,el) VALUES (%s,%s,%s,%s,%s,%s,%s)''', (vals_n))
	if telescope == 'INT':
		cur.execute('''INSERT INTO int_focus (date,instrument,focus,tc,df,ac,el) VALUES (%s,%s,%s,%s,%s,%s,%s)''', (vals_n))
except MySQLdb.Error, e: 
	try:
		print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
	except IndexError:
		print "MySQL Error: %s" % str(e)

