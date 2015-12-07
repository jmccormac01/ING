
"""
A script to stop the indi server for finder camera.

James McCormac

usage:
	python stopindi.py
	
alias:
	stopindi
	
	
Version History:
	17/02/14	- Create written and tested		
"""

import subprocess, time, os

# subprocess - to catch the output from ps aux
def subP(comm):
	"""
	A function to call subprocesses and dump the output 
	from the ICS so it doesn't clog up the screen
	
	@rtype: subprocess
	@return p: subprocess for a given command
	"""

	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p

# disconnect the camera
os.system('indi_setprop -p 7624 "QHY CCD QHY5.CONNECTION.DISCONNECT=On"')
time.sleep(5)

# get process id for indiserver to kill it
p=subP('ps aux | grep "indi"')
out,err=p.communicate()

out=out.split('\n')
for i in range(0,len(out)):
	if "indiserver" in out[i]:
		pid=out[i].split()[1]
		print "Killing INDI server PID: %s" % (pid)
		os.system('kill -9 %s' % (pid))
		
print "INDI server stopped!"