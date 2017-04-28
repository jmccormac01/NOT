"""
Script to spit out a night log for NOT/FIES data
"""
import glob as g
from astropy.io import fits

filelist = g.glob('*.fits')
for image in filelist:
    hdr = fits.open(image)[0].header
    print("{} {} {} {}".format(image,
                               hdr['IMAGETYP'],
                               hdr['TCSTGT'],
                               hdr['FIFMSKNM']))
