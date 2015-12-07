#!/usr/bin/env python
"""
#########################################################
#                                                       #
#                 CheckWeather.py v1.1                  #
#                                                       #
#        A script to check WHT weather and return       #
#              when things are good again               #
#                                                       #
#                   James McCormac                      #
#                                                       #
#########################################################

To run the script type:

	cd /home/osa/jmcc/weather/
	./CheckWeather.py

It will then monitor the weather continuously until 
the safe conditons are met:

	- Humidty < 90% and
	- Wind < 80 km/h and
	- Wet/Dry = Dry

This scipt can be stopped by press 'q + ENTER' or hitting 
'ctrl+c' at any time

Revision History:	
	v1.0	10/01/14	- Script written and tested on macbook
	v1.1	28/01/14	- Script updated to use Weather class 
		28/01/14	- and remove dependency on nltk
		28/01/14	- Tested on OSADISPLAY2 

"""

#: import modules
import time, os, os.path, time, sys, signal, select, subprocess
from datetime import datetime


#: check for debuggin mode
#: define location of audio file
if "debug" in sys.argv:
	DEBUG = 1
	audio_command = "afplay /Users/James/Documents/OpenEyeSignal.mp3"
else:
	DEBUG = 0
	audio_command = "play /usr/share/sounds/purple/alert.wav"


#: Class to store the weather info in
class Weather(object):
	"""
	A class containing the WHT weather information
    """

	def __init__(self, logtime, hum, wind, rain):
		self.logtime = logtime
		self.hum = hum
		self.wind = wind
		self.rain = rain
		
	def __str__(self):
		"""
		Create a human readable representation of the object
		"""
		if self.rain == 1:
			return "LogTime: %s  Hum: %.1f  Wind: %.1f  Rain: yes" % (self.logtime,self.hum, self.wind)
		elif self.rain == 0:
			return "LogTime: %s  Hum: %.1f  Wind: %.1f  Rain: no" % (self.logtime,self.hum, self.wind)
		else:
			return "LogTime: %s  Hum: %.1f  Wind: %.1f  Rain: N.A." % (self.logtime,self.hum, self.wind)
			
		
	def setWeather(self,logtime,hum,wind,rain):
		"""
		Set the weather values
		"""	
		
		self.logtime = logtime
		self.hum = hum
		self.wind = wind
		self.rain = rain
			
	def getWeather(self):
	
		return self.logtime,self.hum, self.wind, self.rain


#: trap ctrl+c
def signal_handler(signal,frame):
	print '\tCtrl+C caught, quitting...'
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
	
	
#: stop the sounds playing
def check_if_need_to_quit():
	x,a,b=select.select([sys.stdin], [], [], 0.001)
	if (x):
		char=sys.stdin.readline().strip()
		if char[0] == 'q':
			sys.exit(0)
	
	return 0


#: Run subprocesses
def subP(comm):
	p = subprocess.Popen(comm, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
	return p
	

#: get the weather file, make sure it exists	
def GetWeatherFile():
	"""
	Get the date in the right format for finding 
	the weather information. 
	
	e.g. if today is YYYY-MM-DD
	weatherfile = DD-MM-YYYY.DAT
	
	@rtype: string
	@return weatherfile: The name of the current weather file
	"""
	
	wfile="/home/skyview/newMetSystem/WHT/%s.DAT" % (time.strftime("%m-%d-%Y"))
	
	#print "Weather File: %s" % wfile
	
	while os.path.exists(wfile) == False:
		print "No weather log file, waiting..."
		time.sleep(60)
		
	return wfile


#: get the data and log it in Weather()
def GetData(w,wfile):
	"""
	Read in the last line of the weather file and check
	that the data is within the last ~5 minutes. 
	
	@param w: instance of Weather() class
	@param wfile: A string with the current weather filename
	@rtype: string
	@return data: A string containing the current weather, to be checked by CheckData()
	"""

	f=open(wfile).readlines()
	data=f[-1]

	t_log=data.split()[0]
	hum=float(data.split()[-2])
	wind=float(data.split()[-4])
	rain=int(data.split()[-1])

	w.setWeather(t_log,hum,wind,rain)

	return 0
	

#: check the weather in w is ok	
def CheckData(w):
	"""
	Check the weather in w.
	
	@param w: instance of Weather() class
	@rtype: integer
	@return data: An integer saying if the weather is good (0) or bad (1)
	"""	
	ok = 0 
	
	if w.hum >= 90.0:
		ok += 1
	if w.wind >= 80.0:
		ok += 1
	if w.rain == 1:
		ok += 1
		
	if ok > 0:
		return 1	

	else:
		return 0


#: Loop to play sounds until stopped
def LoopAlert():
	
	while (1):
		check_if_need_to_quit()
		p=subP('%s' % (audio_command))
		print "BEEP!  (type 'q + ENTER' - or - 'ctrl+c' to quit!)"
		time.sleep(5)
		
	return 0
	
		
#: main function
def main():	
	#: initialise Weather with bad weather info, 100% hum, 100 km/h wind and rain = yes
	w=Weather("00:00:00",100,100,"yes")
	ok = 1
	
	while ok > 0:
		#: get the weather data
		if DEBUG == 0:
			wfile=GetWeatherFile()
		else:
			wfile = "/Users/James/Documents/ING/Scripts/Weather/SampleORMWeather.txt"
		
		data=GetData(w,wfile)
		ok=CheckData(w)
		
		if ok == 0:
			print "%s - Weather is good" % (w)
			break
		if ok != 0:
			print "%s - Weather is bad" % (w)
			time.sleep(5)
		
	print "\nWeather good at %s\n" % (datetime.now().isoformat().split('T')[1][:-7])	
	LoopAlert()


#: run main when called by interpreter
if __name__ == "__main__":
	main()


	