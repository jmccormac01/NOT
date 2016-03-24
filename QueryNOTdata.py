'''
Script to make a list of objects from a bunch of NOT/FIES data

Notes:
	IMAGETYP headers:
		COUNTTEST: Calibration Test
		WAVE: Arc
		FLAT: FLAT
		'  ': Science <-- These are the interesting ones!
'''

import os
import glob as g
from astropy.io import fits
from collections import defaultdict
from contextlib import contextmanager

@contextmanager 
def cd(path): 
	old_dir = os.getcwd() 
	os.chdir(path) 
	try:
		yield 
	finally:
		os.chdir(old_dir) 

top_dir=os.getcwd()
t=g.glob('NOT_20*')
target=defaultdict(list)
imagetyp=defaultdict(list)
for j in range(0,len(t)):
	print('Moving into %s' % (t[j]))
	with cd('%s/fies/' % (t[j])):
		t2=g.glob('FI*.fits*')
		for i in range(0,len(t2)):
			with fits.open(t2[i]) as hdu:
				obj_id=hdu[0].header['TCSTGT']
				image_typ=hdu[0].header['IMAGETYP']
				if image_typ=='':
					target[obj_id].append(t2[i])
				imagetyp[image_typ].append(t2[i])

# print a list of targets and 
# the number of spectra
for i in sorted(target.keys()):
	print i,len(target[i])