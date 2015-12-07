
#########################################################
#                                                       #
#                  	 do_obs.py v1.5                     #
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
#   v1.4   26/08/13 - Script now checks that new filename is used for analysis
#                     and if the new file isn't yet written to disk, it will 
#                     wait for 0.3 sec and try again until a new file is found 
#                     Fixed code so it will only look for files named r*.fit 
#                     Added log-file, it will write to the home directory in a
#                     file named guidelog_YYYYMMDD.txt       
#                     Added option to indicate current dRA and dDEC     
#                     Added option to provide reference frame
#                     Added an offset arc 0 0 when exiting script
#                     Changed the on-screen output 
#                     Made some fixes which should make it compatible with both
#                     Python 2.7 & 3.x  --EdM   
#   v1.5   18/10/13 - Fixed bug that caused a crash when the image was still 
#                     being written to disk
#                     
#                     
#
#   To do:
#       Test on sky - done 20130801, 20130818
#       Add bad pixel map
#
#   Usage:
#   python do_obs.py exposure_time [x0 y0 box_size dRA dDEC directory_for_data reg_file] 
#       exposure_time       -   exposure time in seconds
#       x0, y0              -   approximate coordinates of star to guide
#                               if either is omitted or is set to less than 
#                               (boxsize+30) from the edge of the image, 
#                               the code will search for the brightest star
#                               in the field.
#                               NOTE: this is very time-consuming, and should be
#                               avoided if possible
#       box_size            -   half-size of the box used for the guiding
#                               should be large enough to include the full PSF
#                               By default the box-size is set to 60 pixels
#       dRA                     Current RA offset for offset arc
#       dDEC                    Current DEC offset for offset arc
#       directory_for_data  -   directory where the data are stored. If not 
#                               provided, the code will use the latest directory
#                               in /obsdata/inta/ 
#   
#       ref_file            -   Reference file, when restarting the script
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


def print_usage():
   print("USAGE: python do_obs.py exposure_time [x0 y0 box_size dRA dDEC directory_for_data reg_file] \n")
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
   print("    dRA                        Current RA offset for offset arc")
   print("    dDEC                       Current DEC offset for offset arc")
   print("    directory_for_data   -     directory where the data are stored. If not ")
   print("                               provided, the code will use the latest directory")
   print("                               in /obsdata/inta/ \n")
   print("    ref_file             -     Reference file, when restarting the script")


def sorted_ls(path):
    items=list(sorted(os.listdir(path)))
    newlist = []
    for names in items:
       if names.endswith(".fit") and names.startswith("r"):
          newlist.append(names)
    return newlist


def check_if_need_to_quit():
   x,a,b=select.select([sys.stdin], [], [], 0.001)
   if (x):
     char=sys.stdin.readline().strip()
     if char[0] == 'q':
        ## Python 3.x: input()
        ## Python 2.7: raw_input()
        ##WORKAROUND REMOVAL OF RAW_INPUT IN PYTHON 3
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


def do_obs(texp,xc0,yc0,boxsize,dra,ddec,indir,ref_file):
   ## some definitions and input files
   
   #no hot pixelmap yet...
   #bpm = pf.getdata("hpm.fits")
   #w_bad = np.where(bpm == 0)
   
   # open logfile  
   # file is called ~/guidelog_YYYYMMDD.log wit YYYYMMDD for start of the night 
   ### NOTE THIS IS UGLY CODE... ###
   date=time.gmtime()
   date=[date.tm_year,date.tm_mon,date.tm_mday,date.tm_hour]
   if date[3] < 13:
      date[2] = date[2]-1   ##correct to start of the night
      if date[2] < 1:          
         date[1]=date[1]-1
         if date[1] < 1:
            date[0]=date[0]-1
            date[1]=12
         if any(x == date[1] for x in [1,3,5,7,8,10,12]):
            date[2]=31
         elif any(x == date[1] for x in [4,6,9,11]):
            date[2]=30
         else:
            if ( (date[0]%4 == 0) and (date[0]%100!=0)) or (date[0]%400==0):
               date[2]=29
            else:
               date[2]=28
   logfile=( '%s/guidelog_%4i%02i%02i.txt' % (os.path.expanduser("~"),date[0],date[1],date[2]) )
   if os.path.exists('%s' % logfile) == False:
      log=open('%s' % logfile, 'w')
      log.write("Guiding log night of %4i-%02i-%02i \n" % (date[0],date[1],date[2]))
      log.write("    DATE      TIME         XC     YC         DX     DY       dRA    dDEC      Filename\n ")
      log.write('    (UT)      (UT)                                           (")    (") \n')
   else:
      log=open('%s' % logfile, 'a')

   new_ref=1
   if len(ref_file) > 10:
      if ref_file.endswith(".fit") and ref_file.startswith("r"):
         if os.path.exists("%s/%s" % (indir,ref_file)):
            new_ref=0

   if new_ref:
      #Take first science frame
      os.system( ("run %i" % texp) )
      time.sleep(5)   ##give it some time to write the file to disk 
                      ##<- longer wait to make sure file is written before start of analysis
   
      #get directory listing
      filelist=sorted_ls(indir)
      filename=filelist[-1]
      prev_file=filename
   else:
      filelist=sorted_ls(indir)
      filename=ref_file
      prev_file=filelist[-1]
   ref_file=prev_file

   #read first image and find center of brightest star, check whether image is windowed or not
   #if windowed, pick extension 1 else pick extension 4.
   hdu=pf.open("%s/%s" % (indir,filename))
   img=hdu[len(hdu)-1].data
   if len(hdu) == 5:
      windowed=0
      has_oc=0
   else:
      windowed=1
      has_oc=hd[1].header.get('BIASSEC',0)
   if has_oc:                            ##In windowed mode, including the overscan section causes the window to rotate
      img=np.swapaxes(img[::-1],0,1)     ##This should rotate it back



   xsize=img.shape[1]  # <- Python/Pyfits can be annoying...
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

   print(" FRAME   XC     YC         DX       DY       dRA   dDEC ")
   print('                                             (")    (") ')
   print(' %4i   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s' % (0,xc0,yc0,0.,0.,dra,ddec,filename)) 
   log.write('%s  %s   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s  REFERENCE \n' % (hdu[0].header['DATE-OBS'],hdu[0].header['UT'],xc0,yc0,0.,0.,dra,ddec,filename)) 
   i=0
   quit=0
   while quit != 1:
      os.system( ("run %i" % texp) )
      if check_if_need_to_quit():
         break
      i=i+1
      sys.stdout.flush()

 
      filelist=sorted_ls(indir) 
      filename=filelist[-1]
      while filename == prev_file:
         time.sleep(0.4)
         filelist=sorted_ls(indir) 
         filename=filelist[-1]
      prev_file=filename

      #print("Starting recentering on file %s" % filename)
      #img=pf.getdata("%s/%s" % (indir, filelist[-1]))
      hdu=pf.open("%s/%s" % (indir,filename))
      img=hdu[-1].data
      if has_oc:                            ##In windowed mode, including the overscan section causes the window to rotate
         img=np.swapaxes(img[::-1],0,1)     ##This should rotate it back
     
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
      #print("Star now at  location (%6.1f,%6.1f)"%(xc,yc))
      #print("This is an offset of (%7.2f,%7.2f) pixels from previous"%(dy,dx))
      #print("                     (%7.2f,%7.2f) arcsec from previous"%(dy*0.333,dx*0.333))
      #print("Applying an offset of (%7.2f,%7.2f) arcsec (n.b. offset is cumulative)"%(dra,ddec))
      print(' %4i   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s' % (i,xc,yc,dy,dx,dra,ddec,filename)) 
      log.write('%s  %s   %6.1f %6.1f   %7.2f %7.2f   %7.2f %7.2f   %s \n' % (hdu[0].header['DATE-OBS'],hdu[0].header['UT'],xc,yc,dy,dx,dra,ddec,filename)) 
      sys.stdout.flush()
      os.system( ('offset arc %6.2f  %6.2f' % (dra,ddec)) )
      time.sleep(1)
      #if i % 5 == 0:
      #print ('starting on exposure % 4d' % (i))
   
   tm=time.gmtime()
   date=time.strftime('%Y-%m-%d',tm)
   tm=time.strftime('%H:%M:%S',tm)
   log.write( '%s %s  Quiting Guide Script \n' % (date,tm) )
   log.close()
   print("===END OF THE SCRIPT===" )
   print("LAST OFFSET GIVEN: %6.2f %6.2f" % (dra,ddec) )
   print("RETURING TO NOMIMAL POINTING\n")
   os.system( ('offset arc %6.2f  %6.2f' % (0.,0.)) )
   print("If you want to restart the script with the same target:" )
   print("  - Provide the reference file %s" % ref_file)
   print("  - Provide the dRA and dDEC indicated above" )



## check how many exposures
args=sys.argv
n_arg=np.size(args)
if len(sys.argv) < 2:
   print_usage()
   sys.exit(1)
if n_arg < 4:
   texp=np.float(args[1])
   x0=-1
   y0=-1
   boxsize=50
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
   ref_file=''
   dra=0.
   ddec=0.
elif n_arg == 4:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=50
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
   ref_file=''
   dra=0.
   ddec=0.
elif n_arg == 5:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
   ref_file=''
   dra=0.
   ddec=0.
elif n_arg == 7:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   dra=args[5]
   ddec=args[6]
   tmp=list(sorted(os.listdir('/obsdata/inta/')))
   indir='/obsdata/inta/'+tmp[np.shape(tmp)[0]-1]+'/'
   ref_file=''
elif n_arg == 8:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   dra=np.float(args[5])
   ddec=np.float(args[6])
   indir=args[7]
   ref_file=''
elif n_arg == 9:
   texp=np.float(args[1])
   x0=np.float(args[2])
   y0=np.float(args[3])
   boxsize=np.float(args[4])
   dra=np.float(args[5])
   ddec=np.float(args[6])
   indir=args[7]
   ref_file=args[8]
else:
   print_usage()
   sys.exit(1)
print("using an exposure time of %5.1f seconds" % texp)
print("Initial position estimate is %5.1f,%5.1f" % (x0,y0))
print("using a box-size of %5.1f pixels" % boxsize)
print("using directory " + indir)
print("using reference file " + ref_file)
print("Current offset: %6.1f %6.1f" % (dra,ddec) )
print("Press q to abort the observations.\n \n")

sys.stdout.flush()
do_obs(texp,x0,y0,boxsize,dra,ddec,indir,ref_file)