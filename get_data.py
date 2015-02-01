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

### Create folder for storing data
baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(baspy_path):
	os.makedirs(baspy_path)

### Directories
cmip5_dir = '/badc/cmip5/data/cmip5/output1/'


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
	
	Read CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue()
	   
	refresh = True: refresh CMIP5 cataloge
	   >>> cat = cmip5_catalogue(refresh=True)
	   
	"""
	
	### Location of catologue file
	cat_file = baspy_path+'/cmip5_catalogue.txt'
	
	if (refresh == True):
	
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
    
    
    
def cmip5_cubes(filt_cat, file_yr_range=None):
	"""
	Get CMIP5 data and create multi-ensemble mean for 
	one specified experiment & experiment & variable

	Use file_yr_range to read only files which include fields within range, 
	this will help reduce the number of files read.
	* file_yr_range = [1979,1981]

	"""
	
	for i in range(0,filt_cat.size):
                
                filt = np.array(filt_cat)	
		if (filt.size > 1): filt = filt[i]

		dir = ( ''+str(filt['Centre'])+'/'
			''+str(filt['Model'])+'/'
			''+str(filt['Experiment'])+'/'
			''+str(filt['Frequency'])+'/'
			''+str(filt['SubModel'])+'/Amon/'
			''+str(filt['RunID'])+'/latest/'
			''+str(filt['Var'])+'/' )
		
		netcdfs = os.listdir(cmip5_dir + dir)

		if (netcdfs.__class__ == 'str'): netcdfs = [netcdfs]
	
		run = str(filt['RunID'])
		var = str(filt['Var'])			

		### SPECIAL CASE: AMIP IPSL-CM5A-LR r2i1p1 & r3i1p1 have duplicated data, both in one
		###					netcdf file and split-up amoung many files 
		if ( all( [ len(netcdfs) > 1
				,'tas_Amon_IPSL-CM5A-LR_amip_'+run+'_197901-200912.nc' in netcdfs] )):
			print('>> Fix for '+model+' '+run+' <<')
			netcdfs = ['tas_Amon_IPSL-CM5A-LR_amip_'+run+'_197901-200912.nc']
		
		### make sure that the run id is present in all your 
		### netcdf filenames and that files endswith '.nc' 
		### (Note: EC-Earth also has '*.nc4' files present)
		for nc in netcdfs:
			if all([run in nc, nc.endswith('.nc')]): 
				### Filter out nc files which lie outisde file_yr_range
				if (file_yr_range != None):
					file_last_yr  = np.float(nc[-9:-3])
					file_first_yr = np.float(nc[-16:-10])
					if (file_last_yr  < ((file_yr_range[0]*100) +1) ):
						netcdfs.remove(nc)
					if (file_first_yr > ((file_yr_range[1]*100)+12) ):
						netcdfs.remove(nc)
			if (run not in nc): 
				print('>> Misplaced netcdf files found in '+dir+' <<')
	
		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		for j in netcdfs:
			dirfilename = cmip5_dir + dir + j
			### contraint by var_name
			var_name_con = iris.Constraint(cube_func=lambda cube: cube.var_name == var)
			cube = iris.load_cube(dirfilename, callback=cmip5_callback, constraint=var_name_con)
			### Remove attributes to enable cubes to concatenate
			cube.attributes.clear()
		
			if (j == netcdfs[0]): cubelist1 = iris.cube.CubeList([cube])
			if (j != netcdfs[0]): cubelist1.extend([cube])
		
		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Extract period only
		#con = iris.Constraint(season_year=lambda y: START_YEAR <= y <= END_YEAR)
		#cube = cube.extract(con)
		
		#### Create a cubelist from cubes
		if (i == 0): 
			cubelist2 = iris.cube.CubeList([cube])
		else:
			cubelist2.extend([cube])

	### Return cube
	return cubelist2

# End of get_data.py
