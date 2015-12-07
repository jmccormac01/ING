
#########################################################
#                                                       #
#                  	 logfocus.py v1.1                   #
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
#
#   To do:
#		- Need to add ELEVATION to wht_focus table
#		- Write a plotting script to plot the values between
#		  dates X and Y
#		- Add argparse and ParameterNoticeBoard for EL
#		- Add final error checking
#	   
# 	*** NEEDS TESTED ON OSADISPLAY1 & 2 AND TAURUS
# 

import argparse as ap
import MySQLdb
import sys, os


# argparse assumes type=string unless told otherwise
def ArgParse():
	
	# A function to parse the command line in efficient 
	# way using argparse. 
	#
	# @rtype: list
	# @return args - A list of command line arguments
	
	parser=ap.ArgumentParser()
	parser.add_argument("instrument", help="name of instrument which has been focused e.g. acam")
	parser.add_argument("focus", help="focus value in mm. e.g. 98.00")
	parser.add_argument("tc", help="temperature compensation value at time of focusing")
	parser.add_argument("df", help="defocus value at the time of focusing")
	args=parser.parse_args()
		
	return args

# get the elevation of the t/s
def GetElevation():

	el=os.popen('ParameterNoticeBoardLister -i TCS.alt').readline().split('\n')[0]	
	
	el="%.2f" % (float(el))
	
	return el


args=ArgParse()
#if len(sys.argv) < 5:
#	print "usage: python logfocus.py instrument focus tc df"
#	sys.exit()


# list of available instruments
# check the one entered it correct
inst_list=['ACAM','AF2','CANARY','EXPO','GHAFAS','INTEGRAL','INGRID','ISIS','LIRIS','NAOMI','PFIP','PLANETPOL','PNS','SAURON','ULTRACAM']

if args.instrument.upper() not in inst_list:
	print "\n\t%s not in instrument list. Check spelling?" % (args.instrument.upper())
	print "\tInstrument List: "
	print "\t" + str(inst_list[0:5])[1:-1]
	print "\t" + str(inst_list[5:10])[1:-1]
	print "\t" + str(inst_list[10:-1])[1:-1]
	print "\tExiting...\n"
	sys.exit()


# add a check for stange focus values
# make an array with typical values and then allow +/- 5mm on that
# if more suggest double checking
# same for TC,DF
# EL comes from paramnoticeboard so should be fine
# need to check what happens if that is ever off line


# get the date today
from datetime import datetime
t=datetime.today().isoformat()[:10]

# connect to focus database
db=MySQLdb.connect(host='dbstore.ing.iac.es',user='jmcc',passwd='!jmcc!', db='focus')

# get database cursor
cur=db.cursor()

fields=['date','instrument','focus','tc','df','el']
vals=[]

vals.append(t)
vals.append(args.instrument.upper())
vals.append(args.focus)
vals.append(args.tc)
vals.append(args.df)
el=GetElevation()
vals.append(el)

# make the list a tuple
vals_n=tuple(vals)

# loop over the 6 things to include

try:
	cur.execute('''INSERT INTO wht_focus (date,instrument,focus,tc,df,el) VALUES (%s,%s,%s,%s,%s,%s)''', (vals_n))
except MySQLdb.Error, e: 
	try:
		print "MySQL Error [%d]: %s" % (e.args[0], e.args[1])
	except IndexError:
		print "MySQL Error: %s" % str(e)

