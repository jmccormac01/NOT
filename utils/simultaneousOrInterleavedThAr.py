"""
Script to check if a night has simultaneous ThAr or not
"""
import os
import glob as g
from astropy.io import fits

nights = g.glob('NOT_2*')
for night in nights:
    simult = 0
    normal = 0
    total = 0
    os.chdir(night)
    images = g.glob('*.fits')
    for image in images:
        with fits.open(image) as ff:
            hdr = ff[0].header
            target = hdr['TCSTGT']
            if target != "":
                try:
                    comment = str(hdr['COMMENT'])
                    simult += 1
                except KeyError:
                    normal += 1
                total += 1
            else:
                continue
    print("{} Normal: {} SimultThAr: {} Total: {}".format(night, normal,
                                                          simult, total))
    os.chdir('../')
