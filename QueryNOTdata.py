'''
Script to make a list of objects from a bunch of NOT/FIES data
'''

import os
import glob as g
from astropy.io import fits
from collections import defaultdict
from contextlib import contextmanager

@con­textman­ag­er 
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

for j in range(0,len(t)):
	with cd('%s/fies/' % (t[j])):
		t2=g.glob('FI*.fits*')
		for i in range(0,len(t2)):
			with fits.open(l[i]) as hdu:
				obj_id=hdu[0].header['TCSTGT']
				target[obj_id].append(t2[i])

#f=open('%s/ObjectsObserved.txt' % (top_dir),'w')
#for i in range(0,len(tar_list_n)):
#	f.write("%s    %s\n" % (tar_list_n[i],tar_count_n[i]))
#	
#f.close()
