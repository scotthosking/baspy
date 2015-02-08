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
cmip5_dir = '/badc/cmip5/data/cmip5/output1/'


def cmip5_catalogue(refresh=None):
	"""
	
	Read CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue()
	   
	refresh = True: refresh CMIP5 cataloge
	   >>> cat = cmip5_catalogue(refresh=True)
	   
	"""
	
	### Location of catologue file
	cat_file = baspy_path+'/cmip5_catalogue.npy'
	
	if (refresh == True):
	
		### Get paths for all CMIP5 models and their experiments
		dirs = glob.glob(cmip5_dir+'*/*/*/*/atmos/Amon/*/latest/*')
		dirs2 = glob.glob(cmip5_dir+'*/*/*/*/seaIce/OImon/*/latest/*')
		dirs.extend(dirs2)
		dirs = filter(lambda f: os.path.isdir(f), dirs)

		### Convert list to numpy array
		dirs = np.array(dirs, dtype=str)

		### Only return paths where experiment exists
		centre_str   = np.chararray(len(dirs), itemsize=14)
		model_str    = np.chararray(len(dirs), itemsize=14)
		exp_str      = np.chararray(len(dirs), itemsize=14)
		freq_str     = np.chararray(len(dirs), itemsize=14)
		submodel_str = np.chararray(len(dirs), itemsize=14)
		miptable_str = np.chararray(len(dirs), itemsize=14)
		run_id_str   = np.chararray(len(dirs), itemsize=14)
		var_str      = np.chararray(len(dirs), itemsize=14)

		for i in range(0,len(dirs)):
			split_str = re.split('/',dirs[i])
			centre_str[i]   = split_str[6]
			model_str[i]    = split_str[7]
			exp_str[i]      = split_str[8]
			freq_str[i]     = split_str[9]
			submodel_str[i] = split_str[10]
			miptable_str[i] = split_str[11]
			run_id_str[i]   = split_str[12]
			var_str[i]      = split_str[14]
			
		dt = np.dtype([('Centre', '|S14'), ('Model', '|S14'), ('Experiment', '|S14'), ('Frequency', '|S14'), 
							('SubModel', '|S14'), ('MIPtable', '|S14'), ('RunID', '|S14'), ('Var', '|S14') ])
		a = np.zeros(len(dirs), dt)
		a['Centre']     = centre_str
		a['Model']      = model_str
		a['Experiment'] = exp_str
		a['Frequency']  = freq_str
		a['SubModel']   = submodel_str
		a['MIPtable']	= miptable_str
		a['RunID']      = run_id_str
		a['Var']        = var_str

		np.save(cat_file,a)	
	else:
		### Read in CMIP5 catalogue
		cat = np.load(cat_file)
		return cat




### callback definitions should always take this form (cube, field, filename)
def cmip5_callback(cube, field, filename):
    """ A function which adds an "Experiment" coordinate to the cube """
    # Extract the experiment name from the filename
    split_str = re.split('_',filename) # split string by delimiter
    label = split_str[4]
    
    # Create a coordinate with the experiment label in it
    exp_coord = coords.AuxCoord(label, long_name='RunID', units='no_unit')
    # and add it to the cube
    cube.add_aux_coord(exp_coord)
    
    
    
def cmip5_cubes(filt_cat, files_yr_range=None):
	"""
	Get CMIP5 data and create multi-ensemble mean for 
	one specified experiment & experiment & variable

	"""

	if (filt_cat.__class__ != np.ndarray):
		filt_cat = np.array(filt_cat)
		
	for i in range(0,len(filt_cat)):
		
		filt = np.array(filt_cat[i])
		
		dir = ( ''+str(filt['Centre'])+'/'
			''+str(filt['Model'])+'/'
			''+str(filt['Experiment'])+'/'
			''+str(filt['Frequency'])+'/'
			''+str(filt['SubModel'])+'/'
			''+str(filt['MIPtable'])+'/'
			''+str(filt['RunID'])+'/latest/'
			''+str(filt['Var'])+'/' )
		
		netcdfs = os.listdir(cmip5_dir + dir)
		if (netcdfs.__class__ == 'str'): netcdfs = [netcdfs]
		
		model = str(filt['Model'])	
		run   = str(filt['RunID'])
		var   = str(filt['Var'])			
		
		print(dir)
		
		### Remove files from chararray where run id not in 
		### netcdf filenames or remove files that end with '.nc4' 
		### (Note: EC-Earth has '*.nc4' files present)
		del_netcdfs = []	
		for nc in netcdfs:
 			if (run not in nc): 
					print('>> WARNING: Detected misplaced files'
					' in '+dir+' <<')
			if any([run not in nc, nc.endswith('.nc4')]):
				del_netcdfs.append(nc)
			### Filter out nc files which lie outisde files_yr_range
			if (files_yr_range != None):
				file_last_yr  = np.float(nc[-9:-3])
				file_first_yr = np.float(nc[-16:-10])
				if (file_last_yr  < ((files_yr_range[0]*100) +1) ):
					del_netcdfs.append(nc)
				if (file_first_yr > ((files_yr_range[1]*100)+12) ):
					del_netcdfs.append(nc)

		### Remove netcdfs according to del_netcdfs
		for k in del_netcdfs: 
			if (k in netcdfs): netcdfs.remove(k)

		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		for j in netcdfs:
			dirfilename = cmip5_dir + dir + j
			### contraint by var_name
			con  = iris.Constraint(
				cube_func=lambda cube: cube.var_name == var)
			
			### Additional constrains (level, time)
			#if (constraints != None): con = con & constraints
			
			cube = iris.load_cube(dirfilename, callback=cmip5_callback,
														constraint=con)
			
			### Remove attributes to enable cubes to concatenate
			cube.attributes.clear()
			
			### Create cubelist from cubes
			if (j == netcdfs[0]): cubelist1 = iris.cube.CubeList([cube])
			if (j != netcdfs[0]): cubelist1.extend([cube])
		
		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### Remove temporal overlaps
		cubelist1 = bp.util.rm_time_overlaps(cubelist1)

		### Unify lat-lon grid
		cubelist1 = bp.util.unify_grid_coords(cubelist1, cubelist1[0])
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Create a cubelist from cubes
		if (i == 0): 
			cubelist2 = iris.cube.CubeList([cube])
		else:
			cubelist2.extend([cube])

	### Return cube
	return cubelist2

# End of cmip5.py
