
#########################################################
#                                                       #
#                  	 do_obs.py v1.4                     #
#            *tested 20130801 OV, AG, EdM, JMCC*        #
#                     Ernst de Mooij                    #
#		    	checked by James McCormac               #
#                                                       #
#########################################################
#
#   A script to guide the INT using offset arc and 
#   defocused scienc images
#
#   Revision History:	
#   v1.1   26/07/13 - script writen - EdM
#   v1.2   01/08/13 - added ctrl+c trapping - jmcc
#   v1.2.1 01/08/13 - added usage line and fixed print of current file 
#                     added 1 sec sleep after offset arc to avoid telecope
#                     moving during exposure - EdM
#   v1.2.2 01/08/13 - tested on sky, directions confirmed. Small problem with
#                     window size affecting orientation. Speak to ING ENG.
#   v1.3   16/08/13 - added option for user to input star coordinates and
#                     box-size.
#   v1.4   18/08/13 - fixed image size bug - jmcc
#   
#   To do:
#       Test on sky - done 20130801
#       Add bad pixel map
#       Check time between 'run' returning prompt and file fully written to disk
#          to minimise overheads
#
#   Usage:
#      python do_obs.py exposure_time [x0 y0 box_size directory_for_data]
#
#    exposure_time        -     exposure time in seconds
#    x0, y0               -     approximate coordinates of star to guide
#                               if either is omitted, is set to less (boxsize+30) from the 
#                               edge of the image, the code will  search for the brightest star
#                               in the field.
#                               NOTE: this is very time-consuming, and should be avoided if possible
#    box_size             -     half-size of the box used for the guiding
#                               should be large enough to include the full PSF
#                               By default the box-size is set to 50 pixels
#    directory_for_data   -     directory where the data are stored. If not 
#                               provided, the code will use the latest directory
#                               in /obsdata/inta/
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
        q=raw_input('Are you sure you want to quit (y/n)? ')
        while (q[0] != 'y') and (q[0] != 'n'):
           q=raw_input('Are you sure you want to quit (y/n)? ')
        if q[0] == 'y':
           print("exiting")
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


def do_obs(texp,xc0,yc0,boxsize,indir):
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
   hdu=pf.open("%s/%s" % (indir,filelist[-1]))
   img=hdu[len(hdu)-1].data
   if len(hdu) == 5:
      windowed=0
   else:
      windowed=1
   xsize=img.shape[1]
   ysize=img.shape[0]

   # no hot pixels masking yet...
   # img[w_bad]=np.median(img)
   if (xc0 < (boxsize+20) or yc0 < (boxsize+30) or xc0 > (xsize-boxsize-30) or yc0 > (ysize-boxsize-30)):
      print("Finding center of brightest star..")
      sys.stdout.flush()
      xc0,yc0=findbrightstar(img)
   xc0,yc0=findcenter(img,xc0,yc0,boxsize,boxsize+20)
   print("Found bright star at location (%6.1f,%6.1f)"%(xc0,yc0))
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
      sys.stdout.flush()
      time.sleep(3)  # allow some time for file to be written 
 
      filelist=sorted_ls(indir) 
      print("Starting recentering on file "+str(filelist[-1])+"..")
      #img=pf.getdata("%s/%s" % (indir, filelist[-1]))
      hdu=pf.open("%s/%s" % (indir,filelist[-1]))
      img=hdu[-1].data
     
      xc,yc=findcenter(img,xc0,yc0,boxsize,boxsize+20)
      dx=xc-xc0
      dy=yc-yc0
   
      #if windowed:
         ##For INT CCD4 windowed:    DEC^RA>
      #dra=dra-dx*0.333
      #ddec=ddec+dy*0.333
      #else:   
      #   ##For INT CCD4  DEC<- ^-RA
      dra=dra-dy*0.333
      ddec=ddec-dx*0.333
      print("Star now at  location (%6.1f,%6.1f)"%(xc,yc))
      print("This is an offset of (%7.2f,%7.2f) pixels from previous"%(dy,dx))
      print("                     (%7.2f,%7.2f) arcsec from previous"%(dy*0.333,dx*0.333))
      print("Applying an offset of (%7.2f,%7.2f) arcsec (n.b. offset is cumulative)"%(dra,ddec))
      sys.stdout.flush()
      os.system( ('offset arc %6.2f  %6.2f' % (dra,ddec)) )
      time.sleep(1)
      if i % 5 == 0:
         print ('starting on exposure % 4d' % (i))




## check how many exposures
args=sys.argv
n_arg=np.size(args)
if len(sys.argv) < 2:
   print("USAGE: python do_obs.py exposure_time [x0 y0 box_size directory_for_data] \n")
   print("    exposure_time        -     exposure time in seconds")
   print("    x0, y0               -     approximate coordinates of star to guide")
   print("                               if either is omitted or is set to less than ")
   print("                               (boxsize+30) from the edge of the image, ")
   print("                               the code will search for the brightest star")
   print("                               in the field.")
   print("                               NOTE: this is very time-consuming, and should be ")
   print("                               avoided if possible")
   print("    box_size             -     half-size of the box used for the guiding")
   print("                               should be large enough to include the full PSF")
   print("                               By default the box-size is set to 60 pixels")
   print("    directory_for_data   -     directory where the data are stored. If not ")
   print("                               provided, the code will use the latest directory")
   print("                               in /obsdata/inta/ \n")
   sys.exit(1)
if n_arg < 4:
   texp=np.float(args[1])
   x0=-1
   y0=-1
   boxsize=50
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
elif n_arg == 4:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=50
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
elif n_arg == 5:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
else:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   indir=args[5]
print ("using an exposure time of %5.1f seconds" % texp)
print ("Initial position estimate is %5.1f,%5.1f" % (x0,y0))
print ("using a box-size of %5.1f pixels" % boxsize)
print ("using directory " + indir)
print ("Press q to abort the observations.")

sys.stdout.flush()
do_obs(texp,x0,y0,boxsize,indir)