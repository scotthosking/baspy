#!/usr/bin/python

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
upscale_dir = '/group_workspaces/jasmin/upscale'



def upscale_callback(cube, field, filename):

    str_split = re.split("/", filename)

    # Create new coordinates
    job_coord = coords.AuxCoord(str_split[9], long_name='JobID', units='no_unit')
    cube.add_aux_coord(job_coord)
    exp_coord = coords.AuxCoord(str_split[5], long_name='Experiment', units='no_unit')
    cube.add_aux_coord(exp_coord)
    stash_coord = coords.AuxCoord(str_split[8], long_name='Stash', units='no_unit')
    cube.add_aux_coord(stash_coord)
    res_coord = coords.AuxCoord(str_split[6], long_name='Resolution', units='no_unit')
    cube.add_aux_coord(res_coord)

    ### Add season, year coordinate categorisations
    if str_split[7] == 'monthly':
        seasons = ['djf', 'mam', 'jja', 'son']
        iris.coord_categorisation.add_year(cube, 'time', name='year')
        iris.coord_categorisation.add_month_number(cube, 'time', name='month')
        iris.coord_categorisation.add_season(cube, 'time', name='clim_season', seasons=seasons)
        iris.coord_categorisation.add_season_year(cube, 'time', name='season_year', seasons=seasons)

def catalogue(refresh=None, **kwargs):
	"""
	
	Read UPSCALE catalogue for JASMIN
	   >>> cat = catalogue(Experiment='present_climate', Frequency='monthly')
	   
	refresh = True: refresh CMIP5 cataloge
	   >>> cat = catalogue(refresh=True, Experiment='future_climate', Frequency='6hourly')
	   
	"""
	
	### Location of catologue file
	cat_file = baspy_path+'/upscale_catalogue.npy'

	### If cat_file does not exist, then set refresh=True
	if (os.path.isfile(cat_file) == False):
		print("Catalogue of data files does not exist, this may be the first time you've run this code")
		print("Building catalogue now... this could take a few minutes")
		refresh=True

	if (refresh == True):
	
		### Get all paths for all model data
		dirs = glob.glob(upscale_dir+'/GA3/*/*/*/m??s??i???/*')
		dirs = filter(lambda f: os.path.isdir(f), dirs)

		### Convert list to numpy array
		dirs = np.array(dirs, dtype=str)

		### setup character arrays
		GA_str    = np.chararray(len(dirs), itemsize=14)
		exp_str   = np.chararray(len(dirs), itemsize=16)
		res_str   = np.chararray(len(dirs), itemsize=14)
		freq_str  = np.chararray(len(dirs), itemsize=14)		
		stash_str = np.chararray(len(dirs), itemsize=14)
		job_str   = np.chararray(len(dirs), itemsize=14)

		for i in range(0,len(dirs)):
			split_str    = re.split('/',dirs[i])
			GA_str[i]    = split_str[4]
			exp_str[i]   = split_str[5]
			res_str[i]   = split_str[6]
			freq_str[i]  = split_str[7]
			stash_str[i] = split_str[8]
			job_str[i]   = split_str[9]

		dt = np.dtype([('GA', '|S14'), ('Experiment', '|S16'), ('Resolution', '|S14'), 
						('Frequency', '|S14'), ('Stash', '|S14'), ('JobID', '|S14') ])
		a = np.zeros(len(dirs), dt)
		a['GA']         = GA_str
		a['Experiment'] = exp_str
		a['Resolution'] = res_str
		a['Frequency']  = freq_str
		a['Stash']      = stash_str
		a['JobID']	    = job_str

		np.save(cat_file,a)	
	

	### Read catalogue 
	cat = np.load(cat_file)

	### Filter data
	names  = kwargs.viewkeys()

	for name in names:

		uniq_label = np.unique( cat[name] )
		cat_bool   = np.zeros(len(cat), dtype=bool)

		vals = kwargs[name]

		if (vals.__class__ == str): vals = [vals]
		for val in vals:
			if (val not in uniq_label): 
				raise ValueError(val+' not found. See available: '+np.array_str(uniq_label) )
			cat_bool = np.add(cat_bool, (cat[name] == val) )
		cat = cat[cat_bool]
	
	return cat


def get_cubes(filt_cat, constraints=None, debug=False):
	"""
	Use filtered catalogue of UPSCALE data and return a CubeList
	
	>>> cat = bp.upscale.catalogue(Experiment='present_climate', Frequency='monthly')
	>>> cubelist = bp.upscale.get_cubes(cat)
	"""

	### if filt_cat has only one element then 
	### convert to array
	if (filt_cat.__class__ == np.void):
		filt_cat = np.array([filt_cat])
		
	for i in range(0,len(filt_cat)):
		
		filt = np.array(filt_cat[i])
		
		dir = ( '/'+str(filt['GA'])+'/'
			''+str(filt['Experiment'])+'/'
			''+str(filt['Resolution'])+'/'
			''+str(filt['Frequency'])+'/'
			''+str(filt['Stash'])+'/'
			''+str(filt['JobID'])+'/') 
				

		netcdfs = os.listdir(upscale_dir + dir)
		if (netcdfs.__class__ == 'str'): netcdfs = [netcdfs]

		### Remove files from chararray where stash id not contained within 
		### netcdf filenames
		del_netcdfs = []	
		for nc in netcdfs:
			
			if (str(filt['Stash']) not in nc):
					print('>> Information: Detected misplaced file'
					' in '+dir+'. Will ignore it. <<')
					print(filt['Stash'], nc)

					del_netcdfs.append(nc)
				
		### Remove netcdfs according to del_netcdfs
		for k in del_netcdfs: 
			if (k in netcdfs): netcdfs.remove(k)


		cubelist1 = iris.cube.CubeList([])

		for j in netcdfs:
			dirfilename = upscale_dir + dir + j
					
			if (debug == True):
				print('Reading:', dirfilename)

			cube = iris.load(dirfilename, constraints=constraints, callback=upscale_callback)

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


# End of upscale.py
