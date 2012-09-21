# ----------------------------------------------------------------------------------
#								Multdither.py v1.0
#
#				 	 An automated dithering script for ACAM 
#
#								by James McCormac
# ----------------------------------------------------------------------------------
#
# USAGE: python Multdither.py num exptime step
#

# ----------------------------------------------------------------------------------
# 								Update History
# ----------------------------------------------------------------------------------
# 14/04/12 - 	code writen v1.0
# xx/yy/zz - 	TO BE TESTED
#
#

#############################################
#				Modules						#
#############################################

import sys, time, os

#############################################
#				Variables					#
#############################################

st=5

#############################################
#					Main					#
#############################################

if len(sys.argv) < 4:
	print("USAGE: python Multdither.py num exptime step\n")
	sys.exit()

# make checks on numbers coming in


print "[0,0] - Glance 1 %d sec"
os.system('glance acam %d &' % sys.argv[3] )
time.sleep(sys.argv[3]+st)

i=1 
k=0

while i < sys.argv[2]:
	t=sys.argv[4]+(sys.argv[4]*k)
	
	for j in range(0,4):
		if j==0:
			xs=1
			ys=1
		if j==1:
			xs=-1
			ys=-1
		if j==2:
			xs=-1
			ys=1
		if j==3:
			xs=1
			ys=-1

	if i < sys.argv[2]:
		x=t*xs
		y=t*ys
		i=i+1
		
		os.system('tcsuser "autoguide off"')
		os.system("offset arc %d %d" % (x,y))	
		print "[%d,%d] - Glance %d %d sec" % (x,y,i,sys.argv[3])
		time.sleep(5)
		os.system('tcsuser "autoguide on"')
		time.sleep(10)
		os.system("glance acam %d &" % sys.argv[3])
		time.sleep(sys.argv[3]+st)
	
	k=k+1