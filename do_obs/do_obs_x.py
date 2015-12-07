
import argparse as ap
import os, sys, time, select
import numpy as np
from pylab import *
import pyfits as pf
import signal

def SignalHandler(signal, frame):
	"""
	A function to catch ctrl+c - JMcC
	"""
	
	print('   Ctrl+C caught, shutting down...')
	sys.exit(0)

signal.signal(signal.SIGINT, SignalHandler)


def ArgParse():
	"""
	A function to parse the command line in efficient 
	way using argparse. argparse assumes type=string 
	unless told otherwise. action="store_true" makes 
	the token like a True/False switch, it then stores 
	no associated value - JMcC 
	
	@rtype: list, int
	@return args - A list of command line arguments
	@return DEBUG - Token for DEBUGGING or not 
	"""
	parser=ap.ArgumentParser()
	parser.add_argument("datadir", help="path to data") 
	parser.add_argument("reffile", help="name of reference file for autoguiding")
	parser.add_argument("window", help="windowing? (y/n)")
	parser.add_argument("bin", help="binning factor")
	args=parser.parse_args()
	
	
	return args
	
	
def Sorted_ls(path):  
	"""
	A function to sort the files in the data directory - EdM + JMcC
	
	@rtype: list
	@return new_list - a sorted list of fits images
	"""
	
	t=os.listdir(path)
	new_list=[]
	for i in t:
		if i.startswith('r') and i.endswith('.fit'):
			new_list.append(i)

	return sorted(new_list)  	


def GetProjections(indir,ref_file,ext):
	"""
	A function to collapse 2D arrays along X and Y,
	returning 2x 1D projections - JMcC
	"""
	
	h=pf.open("%s/%s" % (indir,ref_file))[ext].data
	
	xproj=np.sum(h,axis=0)
	yproj=np.sum(h,axis=1)
	
	return xproj,yproj



def GetLoc(ref,check,dim,xoy):

	# normalise the arrays
	cyc_ref_proj=ref/min(ref)
	cyc_check_proj=check/min(check)
		
	# pad the arrays
	pad=np.array([1]*len(cyc_ref_proj))
	x_p=np.concatenate((cyc_ref_proj,pad))
	x_n=np.concatenate((pad,cyc_ref_proj))
	y_p=np.concatenate((cyc_check_proj,pad))
	y_n=np.concatenate((pad,cyc_check_proj))
	sums_p=np.empty(len(ref))
	sums_n=np.empty(len(ref))
	
	# slide array past in +ve and -ve directions directions seperately
	for i in range(0,len(ref)):
		if i == 0:
			z_p=np.copy(y_p)
			z_n=np.copy(y_n)
		if i > 0:
			z_p=np.concatenate((np.array(y_p[-i:]),y_p[:-i]))
			z_n=np.concatenate((y_n[i:],np.array(y_n[:i])))
			
		sums_p[i]=np.sum(x_p*z_p)
		sums_n[i]=np.sum(x_n*z_n)
	
	# trim off first negative as its a double of the first positve
	# then reverse the negative sums and combine with the positive 
	# sums to get a cross correlation array
	sums_tot=np.concatenate((sums_n[1:][::-1],sums_p))
	#print len(sums_tot)
	#print len(sums_n) 
	#print len(sums_p)
		
	loc=np.where(sums_tot==max(sums_tot))[0][0]-dim
	low_res_array=np.linspace(loc-1,loc+1,3)		
			
	# fit quadratic to data
	coeffs=polyfit(low_res_array,sums_tot[loc+dim-1:loc+dim+2],2)
	besty=polyval(coeffs,low_res_array)
	solution=-coeffs[1]/(2*coeffs[0])
	
	if xoy == "x": 
		print "X_r: %.2f pixels" % (solution)
	if xoy == "y":
		print "Y_r: %.2f pixels" % (solution)
		
	#plot(cyc_ref_proj,'r-',cyc_check_proj,'b-')
	#show()
	
	solution = "%.2f" % (solution)
	
	return solution, loc, sums_tot


def DoDonuts(indir,ref_file,bin,ext):
	
	# open logfile
	
	total_x=0
	total_y=0
	
	if os.path.exists("%s/%s" % (indir,ref_file)) == True:
		xproj_ref,yproj_ref=GetProjections(indir,ref_file,ext)
		dimx=len(xproj_ref)-1
		dimy=len(yproj_ref)-1
	
	else:
		print("%s/%s does not exist.." % (indir,ref_file))	
		sys.exit()
	# loop for ever until quit	
	
	prev_file=ref_file
	
	q=0
	
	while q != 1:
		sys.stdout.flush()
	
		t=Sorted_ls(indir) 
		new_img=t[-1]
		while new_img == prev_file:
			print("Waiting for new images...")
			time.sleep(5)
			t=Sorted_ls(indir) 
			new_img=t[-1]
		prev_file=new_img
		
		xproj_new,yproj_new=GetProjections(indir,new_img)
		
		# get shift
		solution_x, loc_x, sums_tot_x=GetLoc(xproj_ref,xproj_new,dimx,"x")
		solution_y, loc_y, sums_tot_y=GetLoc(ref_yproj,check_yproj,dimy,"y")
	
	
		# tally shift
		total_x=(total_x+solution_x)*bin*0.333
		total_y=(total_y+solution_y)*bin*0.333
	
		print("Enter the following in pink window:")
		print("offset arc %.1f %.1f" % (total_x,total_y))	

	return 0




args=ArgParse()

if args.window == 'y':
	ext=1
else:
	ext=4

DoDonuts(args.datadir,args.reffile,args.bin,ext)

