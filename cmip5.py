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
import iris.coord_categorisation

### Create folder for storing data
baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(baspy_path):
	os.makedirs(os.path.expanduser(baspy_path))

### Directories
cmip5_dir = '/badc/cmip5/data/cmip5/output1/'


def catalogue(refresh=None, Experiment=None, Frequency=None, Model=None, Var=None):
	"""
	
	Read whole CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue()

	Read filtered CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue(Experiment=['amip','historical'], Var='tas', Frequency=['mon'])
	   
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
							('SubModel', '|S14'), ('MIPtable', '|S14'), ('RunID', '|S14'), 
							('Var', '|S14') ])
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
	
	### Read CMIP5 catalogue and filter data
	cat = np.load(cat_file)
	use_bool = 0
	
	all_exp = np.unique(cat['Experiment'])
	all_frq = np.unique(cat['Frequency'])
	all_mod = np.unique(cat['Model'])
	all_var = np.unique(cat['Var'])
	
	cat_bool = np.zeros(len(cat), dtype=bool)	
	if (Experiment != None):
		if (Experiment.__class__ == str): Experiment = [Experiment]
		for i in range(0,len(Experiment)):
			if (Experiment[i] not in all_exp): raise ValueError('Experiment not found. See available: '+np.array_str(all_exp) )
			cat_bool = np.add(cat_bool, (cat['Experiment'] == Experiment[i]) )
			use_bool = use_bool + 1
		cat = cat[cat_bool]	
		
	cat_bool = np.zeros(len(cat), dtype=bool)
	if (Frequency != None): 
		if (Frequency.__class__ == str): Frequency = [Frequency]
		for i in range(0,len(Frequency)):
			if (Frequency[i] not in all_frq): raise ValueError('Frequency not found. See available: '+np.array_str(all_frq) )
			cat_bool = np.add(cat_bool, (cat['Frequency'] == Frequency[i]) )
			use_bool = use_bool + 1
		cat = cat[cat_bool]
	
	cat_bool = np.zeros(len(cat), dtype=bool)
	if (Model != None): 
		if (Model.__class__ == str): Model = [Model]
		for i in range(0,len(Model)):
			if (Model[i] not in all_mod): raise ValueError('Model not found. See available: '+np.array_str(all_mod) )
			cat_bool = np.add(cat_bool, (cat['Model'] == Model[i]) )
			use_bool = use_bool + 1
		cat = cat[cat_bool]

	cat_bool = np.zeros(len(cat), dtype=bool)
	if (Var != None): 
		if (Var.__class__ == str): Var = [Var]
		for i in range(0,len(Var)):
			if (Var[i] not in all_var): raise ValueError('Var not found. See available: '+np.array_str(all_var) )
			cat_bool = np.add(cat_bool, (cat['Var'] == Var[i]) )
			use_bool = use_bool + 1
		cat = cat[cat_bool]
	
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
    
    # Add year catagorisation
    iris.coord_categorisation.add_year(cube, 'time', name='year')

    
def get_cubes(filt_cat, constraints=None, debug=False):
	"""
	Use filtered catalogue of CMIP5 data and return a CubeList
	
	>>> cat = bp.cmip5.catalogue(Experiment='historical', Frequency='mon', Var='psl')
	>>> cubelist = bp.cmip5.get_cubes(cat)
	
	"""

	### if filt_cat has only one element then 
	### convert to array
	if (filt_cat.__class__ == np.void):
		filt_cat = np.array([filt_cat])
		
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
		
		model = str(filt['Model'])	
		run   = str(filt['RunID'])
		var   = str(filt['Var'])
		
		netcdfs = os.listdir(cmip5_dir + dir)
		if (netcdfs.__class__ == 'str'): netcdfs = [netcdfs]
		
		### Remove hidden files that start with '.'
		nc2 = []
		for nc in netcdfs:
			if (nc.startswith('.') == False): nc2.append(nc)
		netcdfs = nc2
		
		print(dir)
		
		### Remove files from chararray where run id not in 
		### netcdf filenames or remove files that end with '.nc4' 
		### (Note: EC-Earth has '*.nc4' files present)
		del_netcdfs = []	
		for nc in netcdfs:
			
 			if (run not in nc): 
					print('>> WARNING: Detected misplaced files'
					' in '+dir+' <<')
					print(run, nc)
					
			if any([run not in nc, nc.endswith('.nc4')]):
				del_netcdfs.append(nc)
				
		### Remove netcdfs according to del_netcdfs
		for k in del_netcdfs: 
			if (k in netcdfs): netcdfs.remove(k)

		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		cubelist1 = iris.cube.CubeList([])
		for j in netcdfs:
			dirfilename = cmip5_dir + dir + j
			### contraint by var_name
			con  = iris.Constraint(
				cube_func=lambda cube: cube.var_name == var)
			
			### Additional constrains (level, time)
			if (constraints != None): con = con & constraints
			
			cube = iris.load(dirfilename, callback=cmip5_callback,
						constraints=con)

			if (len(cube) > 1): raise ValueError('more than one cube loaded, expected only one!')

			if ( (type(cube) == iris.cube.CubeList) & (len(cube) == 1) ):	
				cube = cube[0]
				
				### Remove attributes to enable cubes to concatenate
				cube.attributes.clear()
				
				### Create cubelist from cubes
				cubelist1.extend([cube])

		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### Remove temporal overlaps
		cubelist1 = bp.util.rm_time_overlaps(cubelist1)

		### Unify lat-lon grid
		#cubelist1 = bp.util.unify_grid_coords(cubelist1, cubelist1[0])
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		if (debug == True): 
			print(cubelist1)
			print(cmip5_dir + dir)
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Create a cubelist from cubes
		if (i == 0): 
			cubelist2 = iris.cube.CubeList([cube])
		else:
			cubelist2.extend([cube])

	### Return cube
	return cubelist2

# End of cmip5.py
