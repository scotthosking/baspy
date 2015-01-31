#!/usr/bin/python
# Filename: get_data.py

import os
import numpy as np
import re
import datetime
import glob, os.path

import baspy as bp
import iris
import iris.coords as coords


def erai_filenames(start_date, end_date, level_str):
	"""
	Get /Path/filenames for ERA-Interim files within date range
	level_str for JASMIN:
		'as' surface variables
		'ap' pressure level variables
	"""
	start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d_%H%M')
	end_datetime   = datetime.datetime.strptime(end_date,  '%Y-%m-%d_%H%M')
	
	filenames = [] # create an empty list, ready to create list of *.nc filenames
	date = start_datetime
	
	### Get all filenames for all 6 hourly fields between start and end, inclusive
	while date <= end_datetime:
		yr       = str(date.year)
		mon      = str("{:0>2d}".format(date.month))
		day      = str("{:0>2d}".format(date.day))
		hr       = str("{:0>2d}".format(date.hour))
		minute   = str("{:0>2d}".format(date.minute))
		date_str = ''.join([yr,mon,day,hr,minute])
		
		file = '/badc/ecmwf-era-interim/data/gg/as/'+yr+'/'+mon+'/'+day+'/ggas'+date_str+'.nc'
		
		filenames.append(file)
		
		# Add 6 hours to read in next file
		time_increment = datetime.timedelta(days=0, hours=6, minutes=0)
		date = date + time_increment  
	
	return filenames


def cmip5_catalogue(refresh=None):
	"""
	
	If refresh = True then refresh CMIP5 cataloge
	Otherwise just just read in cataloge
	
	   >>> cat = cmip5_catalogue()
	   
	"""
	
	### Location of catologue file
	cat_file = 'cmip5_catalogue.txt'
	
	if (refresh == True):
	
		cmip5_dir = '/badc/cmip5/data/cmip5/output1/'

		### Get paths for all CMIP5 models and their experiments
		dirs = glob.glob(cmip5_dir+'/*/*/*/*/*/Amon/*/latest/*')
		dirs = filter(lambda f: os.path.isdir(f), dirs)

		### Convert list to numpy array
		dirs = np.array(dirs, dtype=str)

		### Only return paths where experiment exists
		centre_str   = np.chararray(len(dirs), itemsize=14)
		model_str    = np.chararray(len(dirs), itemsize=14)
		exp_str      = np.chararray(len(dirs), itemsize=14)
		freq_str     = np.chararray(len(dirs), itemsize=14)
		submodel_str = np.chararray(len(dirs), itemsize=14)
		run_id_str   = np.chararray(len(dirs), itemsize=14)
		var_str      = np.chararray(len(dirs), itemsize=14)

		for i in range(0,len(dirs)):
			split_str = re.split('/',dirs[i])
			centre_str[i]   = split_str[6]
			model_str[i]    = split_str[7]
			exp_str[i]      = split_str[8]
			freq_str[i]     = split_str[9]
			submodel_str[i] = split_str[10]
			run_id_str[i]   = split_str[12]
			var_str[i]      = split_str[14]
			
		dt = np.dtype([('Centre', '|S14'), ('Model', '|S14'), ('Experiment', '|S14'), ('Frequency', '|S14'), 
							('SubModel', '|S14'), ('RunID', '|S14'), ('Var', '|S14') ])
		a = np.zeros(len(dirs), dt)
		a['Centre']     = centre_str
		a['Model']      = model_str
		a['Experiment'] = exp_str
		a['Frequency']  = freq_str
		a['SubModel']   = submodel_str
		a['RunID']      = run_id_str
		a['Var']        = var_str

		titles = ['Centre', 'Model', 'Experiment', 'Frequency', 'SubModel', 'RunID', 'Var']
		header = '%-14s %-14s %-14s %-14s %-14s %-14s %-14s' % ( tuple(titles) )
		header = header+'\n'
		np.savetxt(cat_file, a, header=header, comments='', fmt='%-14s %-14s %-14s %-14s %-14s %-14s %-14s')
		
	else:
		### Read in CMIP5 catalogue
		cat = np.genfromtxt(cat_file, names=True, dtype=None)
		return cat



def cmip5_dirs(model, experiment, var, run_id):
	cmip5_dir = '/badc/cmip5/data/cmip5/output1'
	
	### Get paths for all CMIP5 models and their experiments
	dirs = glob.glob(cmip5_dir+'/*/*/*')
	dirs = filter(lambda f: os.path.isdir(f), dirs)
	
	### Convert list to numpy array
	dirs = np.array(dirs, dtype=str)
	
	### Only return paths where experiment exists
	center = np.chararray(len(dirs), itemsize=14)
	model  = np.chararray(len(dirs), itemsize=14)
	exp    = np.chararray(len(dirs), itemsize=14)
	
	for i in range(0,len(dirs)):
		split_str = re.split('/',dirs[i])
		center_str[i] = split_str[6]
		model_str[i]  = split_str[7]
		exp_str[i]    = split_str[8]
	
	ind = ( (exp_str == experiment) & (model_str == model) )
	
	return dirs[ind]


### callback definitions should always take this form (cube, field, filename)
def cmip5_callback(cube, field, filename):
    """ A function which adds an "Experiment" coordinate to the cube """
    # Extract the experiment name from the filename
    split_str = re.split('_',filename) # split string by delimiter
    label = split_str[4]
    
    # Create a coordinate with the experiment label in it
    exp_coord = coords.AuxCoord(label, long_name='Experiment', units='no_unit')
    # and add it to the cube
    cube.add_aux_coord(exp_coord)
    
    
    
def cmip5_model_ensemble(START_YEAR, END_YEAR, directory, var): # height
	"""
	Get CMIP5 data and create multi-ensemble mean for 
	one specified experiment & experiment & variable
	"""
	## Specify directory and filenames
	runs_dir = directory+"/mon/atmos/Amon/"
	
	### Create list of all runs in dir
	listdirs = os.listdir(runs_dir)
	runs = []
	for f in listdirs:
		### only use dirs which start with r and have data for specified variable
		if all([f.startswith('r'), os.path.exists(runs_dir+f+"/latest/"+var)]):
			runs = runs + [f]
	
	for i in range(0,len(runs)):
		print(directory + ' ' + runs[i])
		var_dir = runs[i]+"/latest/"+var+"/"
		netcdfs = os.listdir(runs_dir + var_dir)
		
		### SPECIAL CASE: AMIP IPSL-CM5A-LR r2i1p1 & r3i1p1 have duplicated data, both in one
		###					netcdf file and split-up amoung many files 
		if ( all( [len(netcdfs) > 1
				,'tas_Amon_IPSL-CM5A-LR_amip_'+runs[i]+'_197901-200912.nc' in netcdfs] )):
			print('>> DODGY FIX for '+model+' '+runs[i]+' <<')
			netcdfs = ['tas_Amon_IPSL-CM5A-LR_amip_'+runs[i]+'_197901-200912.nc']
		
		### make sure that the run id is present in all your 
		### netcdf filenames and that files endswith '.nc' 
		### (Note: EC-Earth also has '*.nc4' files present)
		run_nc = []
		for nc in netcdfs:
			if all([runs[i] in nc, nc.endswith('.nc')]): 
				### Filter out nc files which end before 1979
				### (Also fixes problem with time coord in EC-Earth files pre-1950ish)
				file_last_yr = np.float(nc[-9:-3])
				if (file_last_yr >= ((START_YEAR-1)*100.+ 12.) ): run_nc = run_nc + [nc]
			if (runs[i] not in nc): 
				print('>> Misplaced netcdf files found in '+runs_dir+var_dir+' <<')
		
		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		for j in range(0,len(run_nc)):
			filename = runs_dir + var_dir + run_nc[j]
			### contraint by var_name
			var_name_con = iris.Constraint(cube_func=lambda cube: cube.var_name == var)
			cube = iris.load_cube(filename, callback=cmip5_callback, constraint=var_name_con)
			
			### Remove attributes to enable cubes to concatenate
			cube.attributes.clear()
		
			if (j == 0): cubelist1 = iris.cube.CubeList([cube])
			if (j > 0):  cubelist1.extend([cube])
		
		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Extract period only
		con = iris.Constraint(season_year=lambda y: START_YEAR <= y <= END_YEAR)
		cube = cube.extract(con)
		
		#### Create a cubelist from cubes
		if (i == 0): 
			cubelist2 = iris.cube.CubeList([cube])
		else:
			cubelist2.extend([cube])
		
		#### mon-->season (or annual)
		#if any( [period == 'DJF',period == 'MAM',period == 'JJA',period == 'SON',period == 'ANN'] ):
						
			#if any( [period == 'ANN'] ):
				#cube = bp.cube.months2annual(cube)
			#else:
				#cube = bp.cube.months2seasons(cube)
			
				#### Extract specified season
				#cube = cube.extract(iris.Constraint(clim_season=season))

				#### Extract period only
				#con = iris.Constraint(season_year=lambda y: START_YEAR <= y <= END_YEAR)
				#cube = cube.extract(con)

			#### Create time average over record
			#cube = cube.collapsed(['time'], iris.analysis.MEAN)
					
			#### Create a cubelist from cubes
			#if (i == 0): 
				#cubelist2 = iris.cube.CubeList([cube])
			#else:
				#cubelist2.extend([cube])
		
	### Return cube
	return cubelist2, runs

# End of get_data.py
