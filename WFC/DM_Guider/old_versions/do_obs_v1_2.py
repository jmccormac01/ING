
#########################################################
#                                                       #
#                  	 do_obs.py v1.2	                    #
#                     *not tested*                      #
#                     Ernst deMooij                     #
#			 	checked by James McCormac               #
#                                                       #
#########################################################
#
#   A script to guide the INT using offset arc and 
#   defocused scienc images
#
#   Revision History:	
#   v1.1   26/07/13 - script writen - EdM
#   v1.2   01/08/13 - added ctrl+c trapping - jmcc
#
#
#   To do:
#       Test on sky
#       Add bad pixel map
#
# /int/ObservingSystemSupportPackages/python-3.2.2/bin/python3.2
#


import numpy as np
import pyfits as pf
import os, select, sys, time, string
import signal

print("Modules loaded...")

##################################################
############## Ctrl + C Trapping #################
##################################################

def signal_handler(signal, frame):
	print('   Ctrl+C caught, shutting down...')
	os.system('abort &')
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

##################################################

def sorted_ls(path):  ##from http://stackoverflow.com/questions/4500564/directory-listing-based-on-time
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    items=list(sorted(os.listdir(path), key=mtime))
    newlist = []
    for names in items:
       if names.endswith(".fit"):
          newlist.append(names)
       if names.endswith(".fits"):
          newlist.append(names)
    return newlist


def check_if_need_to_quit():
   x,a,b=select.select([sys.stdin], [], [], 0.001)
   if (x):
     char=sys.stdin.readline().strip()
     if char[0] == 'q':
        q=string.lower(raw_input('Are you sure you want to quit (Yes/No)? '))
        while (q[0] != 'y') and (q[0] != 'n'):
           q=string.lower(raw_input('Are you sure you want to quit (Yes/No)? '))
        if q[0] == 'y':
           print "exiting"
           return 1
   return 0


def findcenter(img,xc,yc,boxsize1,boxsize2):
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


def findbrightstar(img):
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


def do_obs(texp,indir):
   ## some definitions and input files
   
   #no hot pixelmap yet...
   #bpm = pf.getdata("hpm.fits")
   #w_bad = np.where(bpm == 0)
   
   #Take first science frame
   os.system( ("run %i" % texp) )
   time.sleep(2)   ##give it some time to write the file to disk <- Needs to be checked how long this is
   
    #get directory listing
   filelist=sorted_ls(indir)
   
   #read first image and find center of brightest star, check whether image is windowed or not
   #if windowed, pick extension 1 else pick extension 4.
   hdu=pf.open(indir+filelist[np.shape(filelist)[0]-1])
   img=hdu[len(hdu)-1].data
   if len(hdu) == 5:
      windowed=0
   else:
      windowed=1
   
   # no hot pixels masking yet...
   # img[w_bad]=np.median(img)
   print "Finding center of brightest star..."
   sys.stdout.flush()
   xc0,yc0=findbrightstar(img)
   xc0,yc0=findcenter(img,xc0,yc0,50,80)
   print "Found bright star at location (%6.1f,%6.1f)"%(xc0,yc0)
   print
   sys.stdout.flush()
   ddec=0.
   dra=0.
   i=0
   quit=0
   while quit != 1:
      os.system( ("run %i" % texp) )
      if check_if_need_to_quit():
         break
      i=i+1
      print "Starting recentering on file"+filelist[np.shape(filelist)[0]-1]+"..."
      sys.stdout.flush()
      time.sleep(2)  # allow some time for file to be written
 
      filelist=sorted_ls(indir) 
      img=pf.getdata(indir+filelist[np.shape(filelist)[0]-1])
      xc,yc=findcenter(img,xc0,yc0,40,80)
      dx=xc-xc0
      dy=yc-yc0
   
      if windowed:
         ##For INT CCD4 windowed:    DEC^RA>
         dra=dra-dx*0.333
         ddec=ddec+dy*0.333
      else:   
         ##For INT CCD4  DEC<- ^-RA
         dra=dra-dy*0.333
         ddec=ddec-dx*0.333
      print "Star now at  location (%6.1f,%6.1f)"%(xc,yc)
      print "Applying an offset of (%7.2f,%7.2f) arcsec (n.b. offset is cumulative)"%(dra,ddec)
      sys.stdout.flush()
      os.system( ('offset arc %6.2f  %6.2f' % (dra,ddec)) )
      if i % 5 == 0:
         print ('starting on exposure % 4d' % (i))




## check how many exposures
args=sys.argv
n_arg=np.size(args)
if n_arg !=3:
   if n_arg != 2:
      texp=10.
   else:
      texp=np.float(args[1])
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
else:
   texp=np.float(args[1])
   indir=args[2]
print ("using an exposure time of %5.1f seconds" % texp)
print ("using directory " + indir)
print ("Press q to abort the observations.")
print
print
sys.stdout.flush()
do_obs(texp,indir)