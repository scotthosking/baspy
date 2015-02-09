#!/usr/bin/python
# Filename: cmip5.py

import os
import numpy as np
import re
import datetime
import glob, os.path

import baspy as bp
import iris
import iris.coords as coords

### Create folder for storing data
baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(baspy_path):
	os.makedirs(os.path.expanduser(baspy_path))

### Directories
upscale_dir = '/group_workspaces/jasmin/upscale'



def upscale_callback(cube, field, filename):
    """ 
    A function which adds a "JobID" coordinate which comes from the filename. 
    """
    str_split = re.split("/", filename)
    ppfile    = str_split[-1]
    label     = ppfile[0:5] # take the first 5 letters as JobID 
    # Create a coordinate with the JobID label in it
    job_coord = coords.AuxCoord(label, long_name='JobID', units='no_unit')
    # and add it to the cube
    cube.add_aux_coord(job_coord)
    
    

def catalogue(refresh=None):
	"""
	
	Read UPSCALE catalogue for JASMIN
	   >>> cat = catalogue()
	   
	refresh = True: refresh CMIP5 cataloge
	   >>> cat = catalogue(refresh=True)
	   
	"""
	
	### Location of catologue file
	cat_file = baspy_path+'/upscale_catalogue.npy'
	
	if (refresh == True):
	
		### Get paths for all CMIP5 models and their experiments
		dirs = glob.glob(upscale_dir+'/x????/*')
		dirs = filter(lambda f: os.path.isdir(f), dirs)

		### Convert list to numpy array
		dirs = np.array(dirs, dtype=str)

		### Only return paths where experiment exists
		JobID_str   = np.chararray(len(dirs), itemsize=14)
		stream_str  = np.chararray(len(dirs), itemsize=14)
		exp_str     = np.chararray(len(dirs), itemsize=14)
		res_str     = np.chararray(len(dirs), itemsize=14)
		
		for i in range(0,len(dirs)):
			split_str = re.split('/',dirs[i])
			JobID_str[i]    = split_str[4]
			stream_str[i]   = split_str[5]
			
			if ( JobID_str[i] in ['xhqij', 'xhqik', 'xhqil', 'xhqin', 'xhqio'] ):
				# present_n96
				exp_str[i], res_str[i] = 'historical', 'N96'

			if ( JobID_str[i] in ['xhqir', 'xhqis'] ):
				# future_n96
				exp_str[i], res_str[i] = 'future', 'N96'
				
			if ( JobID_str[i] in ['xgxqo', 'xgxqp', 'xgxqq'] ):
				# present_n216
				exp_str[i], res_str[i] = 'present', 'N216'
					
			if ( JobID_str[i] in ['xgyid', 'xgyie', 'xgyif'] ):
				# future_n216
				exp_str[i], res_str[i] = 'future', 'N216'
				
			if ( JobID_str[i] in ['xgxqe', 'xgxqf', 'xgxqg', 'xgxqh', 'xgxqi'] ):
				# present_n512
				exp_str[i], res_str[i] = 'present', 'N512'
				
			if ( JobID_str[i] in ['xgxqk', 'xgxql', 'xgxqm'] ):
				# future_n512
				exp_str[i], res_str[i] = 'future', 'N512'
		
		dt = np.dtype([('JobID', '|S14'), ('Stream', '|S14'), ('Experiment', '|S14'), 
					('Resolution', '|S14') ])
		a = np.zeros(len(dirs), dt)
		a['JobID']       = JobID_str
		a['Stream']      = stream_str
		a['Experiment']  = exp_str
		a['Resolution']  = res_str

		### Remove 'unlabeled' items
		keep_ind = ( res_str.startswith('N') )
		a = a[keep_ind]

		np.save(cat_file,a)	
	else:
		### Read in CMIP5 catalogue
		cat = np.load(cat_file)
		return cat

# End of upscale.py
