## check for nltk
#try:
#	import nltk
#except ImportError:
#	print "No nltk module, exiting!"
#	exit()
#	
#from urllib import urlopen
#import time
#import os
#
#audio_file = "/Users/James/Documents/OpenEyeSignal.mp3"
#url_home="http://catserver.ing.iac.es/weather/index.php?miniview=1"
#
#hum = 100
#
#while(hum) >= 90:
#	html_home=urlopen(url_home).read()
#	raw=nltk.clean_html(html_home).split('\n')
#	
#	new=[]
#	for i in range(0,len(raw)):
#		if 'WHT' in raw[i]:
#			loc=i
#			break
#	
#	loc=loc+2
#	hum=int(raw[loc])
#	
#	print "Humidty: %d " % (hum)
#	time.sleep(10)
#	
#	if hum < 90:
#		break
#
#os.system('afplay %s' % (audio_file))
#
#	
#	
#	
# change this to:
#	read the current date and time
# 	find the right weather file
# 	read the data and check it is ok/bad
#	sound alarm etc