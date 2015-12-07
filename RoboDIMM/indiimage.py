
"""
A script to take images with the new finder camera
using the indi camera server.

The indiserver must be running before using this script.
Without the server images cannot be taken

James McCormac

usage:
	python indiimage.py exptime
	
alias:
	image exptime
	
	
Version History:
	17/02/14	- Create written and tested		
"""

import os, time, sys, datetime
import os.path, subprocess
import argparse as ap

def ArgParse():
	"""
	A function to parse the command line in efficient 
	way using argparse. argparse assumes type=string 
	unless told otherwise. action="store_true" makes 
	the token like a True/False switch, it then stores 
	no associated value
	
	@rtype: list
	@return args - A list of command line arguments
	"""
	parser=ap.ArgumentParser()
	parser.add_argument("exptime", type=float, help="Exposure time (s)")
	args=parser.parse_args()

	return args


def subP(comm):
	"""
	A function to call subprocesses and dump the output 
	from the ICS so it doesn't clog up the screen
	
	@rtype: subprocess
	@return p: subprocess for a given command
	"""

	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p
	
	
def CheckForServer():

	p=subP('ps aux | grep "indi"')
	out,err=p.communicate()

	if "indiserver" not in out:
		print "\nINDI server is not running, start it first using:"
		print "osa> startindi\n"
		sys.exit(1)

	if "indiserver" in out:
		return 0


args=ArgParse() 
exptime = args.exptime

running=CheckForServer()
if running != 0:
	print "Problem with INDI server, exiting..."
	sys.exit(1)


os.system('indi_getprop -p 7624 -t %f &' % (exptime+10))
time.sleep(5)
os.system('indi_setprop -p 7624 "QHY CCD QHY5.CCD_EXPOSURE.CCD_EXPOSURE_VALUE=%.2f" &' % (exptime))
time.sleep((exptime+3))

# rename the images
if os.path.exists("QHY CCD QHY5.CCD1.CCD1.fits") == True:
	t=datetime.datetime.now()
	now=t.isoformat()[:19]
	new_name="FinderImage_%s.fits" % (now)
	new_name=new_name.replace(':','-')
	os.system('mv QHY\ CCD\ QHY5.CCD1.CCD1.fits %s' % (new_name))
	os.system('scp %s osa@osadisplay1:~/finder/' % (new_name))
	print "\nImage %s acquired and sent to\n/home/osa/finder/ on osadisplay1" % (new_name)
	print "Run astrometry on the image to correct the pointing"
	print "See notes here: \nhttp://www.ing.iac.es/Astronomy/tonotes/eng/private/RecoverRoboDIMMPointing.php\n"
	os.system('rm -rf %s' % (new_name))

else:
	print "No FINDER IMAGE FOUND, TRY AGAIN..."
