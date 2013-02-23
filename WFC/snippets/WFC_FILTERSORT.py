

# PYTHON MODULE TO SORT WFC FILTERS

import sys
import numpy as np

token = 0

f_db='/Users/James/Documents/ING/Scripts/WFC/autoflat/FilterDB.txt'
f=open(f_db,'r').readlines()

name,BoN,cen_wave,width,num,mimic=[],[],[],[],[],[]

for i in range(0,len(f)):
	name.append(f[i].split()[0])
	cen_wave.append(f[i].split()[1])
	width.append(f[i].split()[2])
	BoN.append(f[i].split()[3])
	num.append(f[i].split()[4])
	mimic.append(f[i].split()[5])
	
f_list=sys.argv[1:]

id_n,cwl_n,wl_n,id_b,cwl_b,wl_b=[],[],[],[],[],[]

# create 2 lists for narrow and broad band filters
for i in range(0,len(f_list)):
	for j in range(0,len(f)):
		if f_list[i] == mimic[j]:
			if BoN[j] == 'B':
				id_b.append(mimic[j])
				cwl_b.append(cen_wave[j])
				wl_b.append(width[j])
			if BoN[j] == 'N':
				id_n.append(mimic[j])
				cwl_n.append(cen_wave[j])
				wl_n.append(width[j])
	
	if f_list[i] not in mimic:
		print "Filter not found: %s" % (f_list[i])
		
		
# sort the two lists
if len(cwl_b) > 0:	
	x=zip(cwl_b,wl_b,id_b)
	x.sort()
	cwl_b,wl_b,id_b=zip(*x)

if len(cwl_n) > 0:
	y=zip(cwl_n,wl_n,id_n)
	y.sort()
	cwl_n,wl_n,id_n=zip(*y)
	
# afternoon	
if token == 0:
	flat_list=list(id_n)+list(id_b)
	print("Afternoon filter order:")
	print(flat_list)

# morning
if token == 1:
	flat_list=list(id_b)[::-1]+list(id_n)[::-1]
	print("Morning filter order:")
	print(flat_list)



	