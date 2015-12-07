
"""
#########################################################
#                                                       #
#                  	 do_obs.py v2.0                     #
#                                                       #
#             Ernst de Mooij & James McCormac           #
#                                                       #
#########################################################

   A script to guide the INT using offset arc and 
   defocused scienc images

   Revision History:	
   v1.1   26/07/13 - script writen - EdM
   v1.2   01/08/13 - added ctrl+c trapping - JMcC
   v1.2.1 01/08/13 - added usage line and fixed print of current file 
                     added 1 sec sleep after offset arc to avoid telecope
                     moving during exposure - EdM
   v1.2.2 01/08/13 - tested on sky, directions confirmed. Small problem with
                     window size affecting orientation. Speak to ING ENG.
   v1.3   16/08/13 - added option for user to input star coordinates and
                     box-size.
   v1.4   26/08/13 - Script now checks that new filename is used for analysis
                     and if the new file isn't yet written to disk, it will 
                     wait for 0.3 sec and try again until a new file is found 
                     Fixed code so it will only look for files named r*.fit 
                     Added log-file, it will write to the home directory in a
                     file named guidelog_YYYYMMDD.txt       
                     Added option to indicate current dRA and dDEC     
                     Added option to provide reference frame
                     Added an offset arc 0 0 when exiting script
                     Changed the on-screen output 
                     Made some fixes which should make it compatible with both
                     Python 2.7 & 3.x  --EdM    

   v2.0   19/02/13 - Big upgrade to v2.0. 
                     Added argparse, better commenting, more modular design in
                     preparation for additon of donuts -JMcC                 

   To do:
       Test on sky - done 20130801, 20130818
       Add bad pixel map

   
"""

import numpy as np
import pyfits as pf
import os, select, sys, time, string
import datetime
import signal
import argparse as ap
	
##################################################
############## Ctrl + C Trapping #################
##################################################

def SignalHandler(signal, frame):
	"""
	A function to catch ctrl+c - JMcC
	"""
	
	print('   Ctrl+C caught, shutting down...')
	os.system('abort &')
	sys.exit(0)

signal.signal(signal.SIGINT, SignalHandler)

##################################################
################## Functions #####################
##################################################	

# argparse assumes type=string unless told otherwise
# 
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
	parser.add_argument("exptime", type=float, help="exposure time (s)")
	parser.add_argument("--debug", help="runs the script in DEBUGGING mode, no system calls made", action="store_true")
	parser.add_argument("--x0y0", type=tuple, help="x y coords of guide star (pix). e.g. (512,486)")
	parser.add_argument("--hbs", type=int, help="half guide box size (pix)")
	parser.add_argument("--dRAdDEC", type=tuple, help="current RA,DEC offset (arcsec). e.g. (10,5)")
	parser.add_argument("--datadir", help="path to data") 
	parser.add_argument("--reffile", help="name of reference file for autoguiding")
	args=parser.parse_args()
	
	if args.debug:
		print "\n**********************"
		print "* DEBUGGING Mode ON! *"
		print "**********************\n"
		DEBUG = 1
	if not args.debug:
		DEBUG = 0
	
	return args, DEBUG

	
def isNumber(s):
	"""
	A function to check if something is or can be a number - JMcC
	
	@param s: A string/number to be checked
	@rtype Boolean
	@return True or False for isNumber
	"""
	try:
		int(s)
		return True
	except ValueError:
		return False


def SetArgs(args,DEBUG):
	"""
	A function to take output of ArgParse() and give us the bits we need - JMcC
	
	@param args: List of arguments for assignment
	@param DEBUG: DEBUGGING mode on/off
	@rtype: int,int,int,float,float,string,string,float
	@return x0,y0 - x and y of guide star
	@return boxsize - half guide box size
	@return dra,ddec - current ra and dec offsets
	@return indir,ref_file - data directory and reference file
	@return texp - exposure time
	"""
	
	# set x0 and y0
	if args.x0y0:
		x0 = int(args.x0y0[0])
		y0 = int(args.x0y0[1])
	else:
		x0 = -1
		y0 = -1	
	
	# set boxsize	
	if args.hbs:
		boxsize = args.hbs
	else:
		boxsize = 50	
			
	# set dRA and dDEC
	if args.dRAdDEC:
		dra = float(args.dRAdDEC[0])
		ddec = float(args.dRAdDEC[1])
	else:
		dra = 0.0
		ddec = 0.0
	
	# set data directory
	# filter rubbish and non-data dirs from list
	if args.datadir:
		indir = args.datadir
	else:
		if DEBUG == 0:
			tmp=os.listdir('/obsdata/inta/')
			ntmp=[]
			for folder in tmp:
				if isNumber(folder):
					ntmp.append(folder)
			ntmp=sorted(ntmp)		
			indir='/obsdata/inta/%s/' % (ntmp[-1])
		else:
			indir='%s' % os.getcwd()
			
	# set reference file
	if args.reffile:
		ref_file=args.reffile
	else:
		ref_file = ""
	
	# set texp
	texp=args.exptime
		
	return x0,y0,boxsize,dra,ddec,indir,ref_file,texp


def GetLogFile():
	"""
	A function to return the name of tonight's logfile - EdM + JMcC
	
	@rtype: string
	@return logfile - the name of the logfile
	"""
	
	date=datetime.datetime.now()
	
	if date.hour<12.0:
		date=date-datetime.timedelta(days=1)
	date_string="%04d-%02d-%02d" % (date.year,date.month,date.day)
	logfile='/home/intobs/guidelog_%s.txt' % (date_string)

	# if the file is new add some stuf at the top
	# otherwise just return the name and open it later with 'a'
	# for appending
	if os.path.exists(logfile) == False:
		os.system('touch %s' % (logfile))
		f=open(logfile,'w')
		f.write("Guiding log for night of %s\n" % (date_string))
		f.write("    DATE      TIME         XC     YC         DX     DY       dRA    dDEC      Filename\n ")
		f.write('    (UT)      (UT)                                           (")    (") \n')
	
	return logfile


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


def FindBrightStar(img):
	"""
	A function to find a bright star for guiding - EdM
	
	@param img: the image in which to find a star
	@rtype int,int
	@return xc0,yc0 - coordinates of a guide star
	"""

	n_im=np.swapaxes(img,0,1)
	n_im=n_im-np.median(n_im)
	w_im=np.array(np.where(n_im > -10000000000))
	i0=np.array(n_im)
	ii=np.reshape(i0,i0.shape[0]*i0.shape[1])
	s_ii=np.argsort(ii)
	s_ii=s_ii[::-1]
	nx=np.shape(n_im[:,0])
	ny=np.shape(n_im[0,:])
	nt=np.shape(ii)
	found=0
	j=0
	
	while found != 1:
		w=[w_im[0,s_ii[j]],w_im[1,s_ii[j]]]
		if (w[0] > 100) and (w[0] < (nx[0]-100)) and (w[1] > 100) and (w[1] < (ny[0]-100)) and (found == 0):
			poststamp=n_im[w[0]-5:w[0]+5,w[1]-5:w[1]+5]
			ww=np.array(np.where(poststamp > (ii[s_ii[j]]*0.5)))
			d=np.shape(ww)[1]
			if d > 10:
				found=1
				xc0=w[0]
				yc0=w[1]
		j=j+1
	
	return xc0,yc0	


def FindCenter(img,xc,yc,boxsize1,boxsize2):
	"""
	A function to find the centre of the guide star - EdM
	
	@param img: the image to centroid
	@param xc,yc: the coordinates of the star
	@param boxsize1,boxszie2: box sizes
	@rtype: float,float
	@return xcn,ycn - centre of the guide star
	"""
	
	n_im=np.swapaxes(img,0,1)
	cutout1=n_im[xc-boxsize1:xc+boxsize1,yc-boxsize1:yc+boxsize1]
	cutout2=n_im[xc-boxsize2:xc+boxsize2,yc-boxsize2:yc-boxsize1]
	med=np.median(cutout2)
	sig=1.5*np.median(np.abs(cutout2-med))
	w_source=np.where( ((cutout1-med)/sig) > 7. )
	
	if np.size(w_source) > 10:
		xcn=np.mean(w_source[0][:])+xc-boxsize1
		ycn=np.mean(w_source[1][:])+yc-boxsize1
	else:
		xcn=xc
		ycn=yc
	
	cutout1=n_im[xcn-boxsize1:xcn+boxsize1,ycn-boxsize1:ycn+boxsize1]
	
	return xcn,ycn
	

def check_if_need_to_quit():
	"""
	A function to check if we want to quit the script
	Looks for q+Enter on the command line while the 
	script is running  - EdM
	"""

	x,a,b=select.select([sys.stdin], [], [], 0.001)
	if (x):
		char=sys.stdin.readline().strip()
		if char[0] == 'q':
			# Python 3.x: input()
			# Python 2.7: raw_input()
			# WORKAROUND REMOVAL OF RAW_INPUT IN PYTHON 3
			if sys.version_info[0] == 2:
				q=raw_input('Are you sure you want to quit (Y/N)? ')
				while (q[0].lower() != 'y') and (q[0].lower() != 'n'):
					q=raw_input('Are you sure you want to quit (Y/N)? ')
				if q[0].lower() == 'y':
					print("exiting")
					return 1
			else:
				q=input('Are you sure you want to quit (Y/N)? ')
				while (q[0].lower() != 'y') and (q[0].lower() != 'n'):
					q=input('Are you sure you want to quit (Y/N)? ')
				if q[0].lower() == 'y':
					print("exiting")
					return 1
					
	return 0
		
		
def do_obs(texp,xc0,yc0,boxsize,dra,ddec,indir,ref_file):
	"""
	A function to take the observation and keep track of the 
	autoguiding using the functions above - EdM
	
	@param texp: exposure time
	@param xc0,yc0: the coordinates of the guide star
	@param boxsize: the size of the guide box
	@param dra,ddec: the offsets already applied in ra and dec
	@param indir: data directory
	@param ref_file: name of the reference image
	@rtype None
	"""
	
	# open log file
	logfile=GetLogFile()
	print "Opening logfile %s..." % (logfile)
	log=open('%s' % logfile, 'a')
	
	# check for reference file
	if ref_file.endswith(".fit") and ref_file.startswith("r") and os.path.exists("%s/%s" % (indir,ref_file)):
		new_ref=0
	else:
		new_ref=1
	
	# take new reference image
	if new_ref:
		print "Taking new reference image..."
		# take first science frame
		os.system( ("run %f" % texp) )
		# wait for it to write to disk
		time.sleep(5)		   
		
		# get directory listing
		filelist=Sorted_ls(indir)
		filename=filelist[-1]
		prev_file=filename
	
	# otherwise use the last image
	else:
		filelist=Sorted_ls(indir)
		filename=ref_file
		prev_file=filelist[-1]
	
	ref_file=prev_file
	
	# read first image and find center of brightest star
	# check whether image is windowed or not
	# if windowed, pick extension 1 else pick extension 4.

	hdu=pf.open("%s/%s" % (indir,filename))
	img=hdu[len(hdu)-1].data
	if len(hdu) == 5:
		windowed=0
		has_oc=0
	else:
		windowed=1
		has_oc=hdu[1].header.get('BIASSEC',0)
	# in windowed mode, including the overscan section 
	# causes the window to rotate
	if has_oc:
		# this should rotate it back                            
		img=np.swapaxes(img[::-1],0,1)     
	
	
	# <- Python/Pyfits can be annoying, y=0
	xsize=img.shape[1]  
	ysize=img.shape[0]
	
	# no hot pixels masking yet...
	# img[w_bad]=np.median(img)
	if (xc0 < (boxsize+20) or yc0 < (boxsize+30) or xc0 > (xsize-boxsize-30) or yc0 > (ysize-boxsize-30)):
		print("Finding center of brightest star...")
		sys.stdout.flush()
		xc0,yc0=FindBrightStar(img)
		xc0,yc0=FindCenter(img,xc0,yc0,boxsize,boxsize+20)
	print("Found bright star at location (%6.1f,%6.1f)" % (xc0,yc0))
	sys.stdout.flush()
		
	# print to screen
	print(" FRAME   XC     YC         DX       DY       dRA   dDEC ")
	print('                                             (")    (") ')
	print(' %4d   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s' % (0,xc0,yc0,0.,0.,dra,ddec,filename)) 
		
	# log info
	log.write('%s  %s   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s  REFERENCE \n' % (hdu[0].header['DATE-OBS'],hdu[0].header['UT'],xc0,yc0,0.,0.,dra,ddec,filename)) 
	i=0
	quit=0
	
	# loop while quit != 1
	while quit != 1:
		os.system( ("run %i" % texp) )
		if check_if_need_to_quit():
			break
		i=i+1
		sys.stdout.flush()
	 	
		filelist=Sorted_ls(indir) 
		filename=filelist[-1]
		while filename == prev_file:
			print("Waiting for new images...")
			time.sleep(0.4)
			filelist=Sorted_ls(indir) 
			filename=filelist[-1]
		prev_file=filename
		
		hdu=pf.open("%s/%s" % (indir,filename))
		img=hdu[-1].data
		
		# if there is overscan, flip axes like before
		if has_oc:                            
			img=np.swapaxes(img[::-1],0,1)     
		 
		xc,yc=FindCenter(img,xc0,yc0,boxsize,boxsize+20)
		dx=xc-xc0
		dy=yc-yc0	   		
		dra=dra-dy*0.333
		ddec=ddec-dx*0.333
		
		print(' %4d   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s' % (i,xc,yc,dy,dx,dra,ddec,filename)) 
		
		# log info
		log.write('%s  %s   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s \n' % (hdu[0].header['DATE-OBS'],hdu[0].header['UT'],xc,yc,dy,dx,dra,ddec,filename)) 
		sys.stdout.flush()
		os.system( ('offset arc %6.2f  %6.2f' % (dra,ddec)) )
		time.sleep(1)
	   
	tm=time.gmtime()
	date=time.strftime('%Y-%m-%d',tm)
	tm=time.strftime('%H:%M:%S',tm)
	log.write( '%s %s  Quiting Guide Script \n' % (date,tm) )
	log.close()
	print("===END OF THE SCRIPT===" )
	print("LAST OFFSET GIVEN: %6.2f %6.2f" % (dra,ddec) )
	print("RETURING TO NOMIMAL POINTING\n")
	os.system( ('offset arc %d  %d' % (0,0)) )
	print("If you want to restart the script with the same target:" )
	print("  - Provide the reference file %s" % ref_file)
	print("  - Provide the dRA and dDEC indicated above" )


def GetProjections(indir,ref_file):
	"""
	A function to collapse 2D arrays along X and Y,
	returning 2x 1D projections - JMcC
	"""
	
	h=pf.open("%s/%s" % (indir,ref_file))[0].data
	
	xproj=np.sum(h,axis=0)
	yproj=np.sum(h,axis=1)
	
	return xproj,yproj


def DoDonuts(texp,dra,ddec,indir,ref_file):
	
	# open logfile
	
	if os.path.exists("%s/%s" % (indir,ref_file)) == True:
		xproj_ref,yproj_ref=GetProjections(indir,ref_file)
	
	else:
		os.system('run %d' % texp)
		time.sleep(5)
		new_img=Sorted_ls(indir)[-1]
		xproj_ref,yproj_ref=GetProjections(indir,new_img)
		
	# loop for ever until quit	
	i=0
	quit = 0
	
	prev_file=new_img
	
	while q != 1:
		os.system( ("run %i" % texp) )
		if check_if_need_to_quit():
			break
		i=i+1
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
		# use FFTs or cyclic?
		# I think cyclic, get code from cyclic in reductions
		x_rel,y_rel=GetShift(xproj_ref,yproj_ref,xproj_new,yproj_new)
	
	
		# tally shift
	
	
		# apply shift
	

	return 0





DONUTS = 1

# main
if __name__ == "__main__":
	args,DEBUG=ArgParse()
	print("Modules loaded...")
	x0,y0,boxsize,dra,ddec,indir,ref_file,texp=SetArgs(args,DEBUG)
	print("Using an exposure time: %.2f s" % texp)
	print("Initial position estimate: %.1f,%.1f" % (x0,y0))
	print("Using a boxsize: %5.1f pixels" % boxsize)
	print("Using directory: %s" % indir)
	print("Using reference file: %s" % ref_file)
	print("Current offset: %.1f %.1f" % (dra,ddec) )
	print("Press q to abort the observations.\n\n")
	sys.stdout.flush()
	if DEBUG == 0:
		do_obs(texp,x0,y0,boxsize,dra,ddec,indir,ref_file,DEBUG)        
	
	if DONUTS == 0:
		DoDonuts(texp,dra,ddec,indir,ref_file)
	
	