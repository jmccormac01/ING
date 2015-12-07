
"""
A script to start the indi server for finder camera.
Without the server images cannot be taken

James McCormac

usage:
	python startindi.py
	
alias:
	startindi
	
	
Version History:
	17/02/14	- Create written and tested		
"""

import os, time

# start the indiserver on port 7624
os.system('indiserver -v -p 7624 -m 100 indi_qhy_ccd &')
time.sleep(5)
# connect to the finder camera using QHY CCD QHY5 camera driver
os.system('indi_setprop -p 7624 "QHY CCD QHY5.CONNECTION.CONNECT=On" &')
time.sleep(2)
# set the gain of the CCD from default of 100 to 10 
os.system('indi_setprop -p 7624 "QHY CCD QHY5.CCD_GAIN.GAIN=10.0" &')
time.sleep(2)
# check the camera is connected and gain is set
os.system('indi_getprop -p 7624 &')

