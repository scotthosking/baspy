#!/usr/bin/python
# Filename: cmip5.py

import os
import numpy as np
import pandas as pd
import re
import datetime
import glob, os.path
import shutil
import baspy as bp
import iris
import iris.coords as coords
import iris.coord_categorisation

cmip5_cat_fname = 'cmip5_catalogue.csv'

### Location of personal catologue file
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))
cat_file = __baspy_path+'/'+cmip5_cat_fname

### If personal catologue file does not exist then copy shared catologue file
__shared_cat_file = '/group_workspaces/jasmin/bas_climate/data/data_catalogues/'+cmip5_cat_fname
if (os.path.isfile(cat_file) == False):	
	print("Catalogue of CMIP5 data does not exist, this may be the first time you've run this code")
	print('Copying shared catalogue to '+__baspy_path)
	shutil.copy2(__shared_cat_file, cat_file)

### Directories
cmip5_dir = '/badc/cmip5/data/cmip5/output1/'

### Originally set cat to nothing
### global cat will be updated for the first time it is read
__cat = []



def catalogue(refresh=None, **kwargs):
	"""
	
	Read whole CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue()

	Read filtered CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue(Experiment=['amip','historical'], Var='tas', Frequency=['mon'])
	   
	refresh = True: refresh CMIP5 cataloge (both personal and shared catalogues)
	   >>> cat = cmip5_catalogue(refresh=True)
	   
	"""
	
	################################
	### Build a new catalogue
	################################

	if (refresh == True):

		print("Building catalogue now... go grab a cuppa, this could take a while...")
	
		### Get paths for all CMIP5 models and their experiments
		model_exp_dirs = glob.glob(cmip5_dir+'*/*/*/*')
		
		dirs = []
		for model_exp in model_exp_dirs:
		    print(model_exp)
		    dirs.extend(glob.glob(model_exp+'/*/*/*/latest/*'))

		dirs = filter(lambda f: os.path.isdir(f), dirs)

		### write data to catalogue (.csv) using a Pandas DataFrame
		rows = []
		for dir in dirs:
		    parts = re.split('/', dir)[6:]
		    parts.pop(7)
		    parts.append(dir)
		    rows.append(parts)

		df = pd.DataFrame(rows, columns=['Centre','Model','Experiment','Frequency','SubModel','MIPtable','RunID','Var','Path'])

		### save to local dir
		df.to_csv(cat_file, index=False)

		### Copy this newly created catalogue to the shared catalogue directory
		### for others to use
		shutil.copy2(cat_file, __shared_cat_file)


	################################
	### Read and filter catalogue
	################################

	### read if not already loaded
	global __cat
	if (len(__cat) == 0): 
		print('### Loading CMIP5 Catalogue ###')
		__cat = pd.read_csv(cat_file) 

		### Check to see if there is a newer version of the catalogue available
		if ( os.path.getctime(__shared_cat_file) > os.path.getctime(cat_file) ):
			print('')
			print('Note: There is a newer version of the CMIP5 catalogue avaiable at')
			print(__shared_cat_file)
			print('although it is safe to continue using the one you are using in '+__baspy_path)
			print('')

	### Filter catalogue
	names = kwargs.viewkeys()

	### TO DO!!!
	#
	#  If Frequency has not been set then default to 'mon'
	#
	#  Print a Warning to this effect
	#

	for name in names:

		uniq_label = np.unique( __cat[name] )
		cat_bool   = np.zeros(len(__cat), dtype=bool)

		vals = kwargs[name]

		### if vals has just 1 element (i.e., is a string) then convert to a list
		if (vals.__class__ == str): vals = [vals]
		if (vals.__class__ == np.string_): vals = [vals]

		for val in vals:
			if (val not in uniq_label): 
				raise ValueError(val+' not found. See available: '+np.array_str(uniq_label) )
			cat_bool = np.add(cat_bool, (__cat[name] == val) )
		__cat = __cat[cat_bool]
	
	# Some Var names are duplicated across SubModels (e.g., Var='pr')
	# Cause code to fall over if we spot more than one unique SubModel
	# when Var= has been set.
	if (len(np.unique(__cat['SubModel'])) > 1) & ('Var' in names):
		print('SubModel=', np.unique(__cat['SubModel']))
		raise ValueError("Var is ambiguous, try defining Submodel (e.g., SubModel='atmos')")

	### As standard, we do not want a cube with multiple Frequencies (e.g., monthly and 6-hourly)
	if (len(np.unique(__cat['Frequency'])) > 1) & ('Var' in names):
		print('Frequency=', np.unique(__cat['Frequency']))
		raise ValueError("Multiple time Frequencies present, try defining Frequency (e.g., Frequency='mon')")

	return __cat





def get_template_cube():
	'''
	Get a cube to use as a CMIP5 template
	'''
	cat  = catalogue(Model='CMCC-CM',Experiment='historical',Var='tas',Frequency='mon')
	con  = iris.Constraint(cube_func=lambda cube: cube.var_name == 'tas') & iris.Constraint(year=2000) & iris.Constraint(month=1)
	cube = get_cubes(cat.iloc[[0]], constraints=con)
	return cube[0]




def cmip5_callback(cube, field, filename):
	"""
	A function which adds a "RunID" coordinate to the cube
	"""

	### Extract the Model name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[2]
	new_coord = coords.AuxCoord(label, long_name='Model', units='no_unit')
	cube.add_aux_coord(new_coord)

	### Extract the Experiment name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[3]
	new_coord = coords.AuxCoord(label, long_name='Experiment', units='no_unit')
	cube.add_aux_coord(new_coord)

	### Extract the RunID name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[4]
	new_coord = coords.AuxCoord(label, long_name='RunID', units='no_unit')
	cube.add_aux_coord(new_coord)

	if (len(cube.coords('time')) > 0): ### this should be generised for recognised time dimensions !!!!

		### Add year catagorisation
		iris.coord_categorisation.add_year(cube, 'time', name='year')
		iris.coord_categorisation.add_month_number(cube, 'time', name='month')

		### Add season
		seasons = ['djf', 'mam', 'jja', 'son']
		iris.coord_categorisation.add_season(cube, 'time', name='clim_season', seasons=seasons)
		iris.coord_categorisation.add_season_year(cube, 'time', name='season_year', seasons=seasons)



def get_cubes(filt_cat, constraints=None, verbose=True):
	"""
	Use filtered catalogue of CMIP5 data and return a CubeList

	>>> cat = bp.cmip5.catalogue(Experiment='historical', Frequency='mon', Var='psl')
	>>> cubelist = bp.cmip5.get_cubes(cat)
	"""

	### start with empty cubelist, then expand within loop
	cubelist2 = iris.cube.CubeList([])

	count = 0
	len_filt = len(filt_cat.index)

	for i in filt_cat.index:
		
		filt   = filt_cat[filt_cat.index == i]
		path   = filt['Path'].values[0]
		model  = filt['Model'].values[0]
		run_id = filt['RunID'].values[0]
		var    = filt['Var'].values[0]
		exp    = filt['Experiment'].values[0]
		
		### Print progress to screen
		if (verbose == True): 
			count = count+1 ### could also add total (e.g., 1 of 101) !!!!!!!!!!!!!!!!!!!!!
			print('['+str(count)+'/'+str(len_filt)+'] CMIP5 '+model+' '+run_id+' '+exp+' '+var)

		netcdfs = os.listdir(path)
		
		### Remove hidden files that start with '.'
		nc2 = []
		for nc in netcdfs:
			if (nc.startswith('.') == False): nc2.append(nc)
		netcdfs = nc2

		
		### Remove files from chararray where run id not in 
		### netcdf filenames or remove files that end with '.nc4' 
		### (Note: EC-Earth has '*.nc4' files present)
		del_netcdfs = []	
		for nc in netcdfs:
			
			if (run_id not in nc):
					print('>> WARNING: Detected misplaced files'
					' in '+path+' <<')
					print(run_id, nc)
					
			if any([run_id not in nc, nc.endswith('.nc4')]):
				del_netcdfs.append(nc)
				
		### Remove netcdfs according to del_netcdfs
		for k in del_netcdfs: 
			if (k in netcdfs): netcdfs.remove(k)

		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		cubelist1 = iris.cube.CubeList([])
		for j in netcdfs:
			dirfilename = path+'/'+j
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

		### Fix EC-Earth
		### turn Gregorian calendars into standard ones
		### !!! assumes that the dates are actually the same in Gregorian and standard calendar
		### (this is definitely true for historical and RCP runs)
		if (model == 'EC-EARTH'):
			if ( (exp.startswith('rcp')) | (exp.startswith('hist')) ):
				# fix calendar
				for cube in cubelist1:
					for time_coord in cube.coords():
						if time_coord.units.is_time_reference():
							if time_coord.units.calendar == u'gregorian':
								time_coord.units = iris.unit.Unit(time_coord.units.origin, u'standard')

			# promote auxiliary time coordinates to dimension coordinates
			for cube in cubelist1:
				for time_coord in cube.coords():
					if time_coord.units.is_time_reference():
						if (time_coord in cube.aux_coords and time_coord not in cube.dim_coords):
							iris.util.promote_aux_coord_to_dim_coord( cube, time_coord )

			iris.util.unify_time_units(cubelist1)

			# remove long_name from all time units
			for cube in cubelist1:
				for time_coord in cube.coords():
					if time_coord.units.is_time_reference():
						time_coord.long_name = None

			for c in cubelist1: c.attributes.clear()

			print('>> Applied EC-Earth fixes <<')

		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### Remove temporal overlaps
		cubelist1 = bp.util.rm_time_overlaps(cubelist1)

		### Unify lat-lon grid
		#cubelist1 = bp.util.unify_grid_coords(cubelist1, cubelist1[0])
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Create a cubelist from cubes
		cubelist2.extend([cube])

	return cubelist2



def get_orog(model):
	'''
	Get Orography for model

		>>> orog = get_orog('HadCM3')

	'''

	### substitute orography for models where file is missing
	### with models with the same orography --- CHECK THESE ARE SAME RESOLUTION!!!!!
	if (model == 'HadGEM2-AO'): model = 'HadGEM2-CC'

	filt_cat = catalogue(Model=model, Frequency='fx', Var='orog')
	exps     = filt_cat['Experiment'].values

	if (len(exps) == 0): raise ValueError('No orography files exists for '+model)

	### whitelist experiments to read orog data from (ordered list)
	whitelist = ['historical', 'piControl', 'amip', 'rcp45', 'decadal1980']

	for wl in whitelist:
		if (wl in exps): 
			orog = get_cubes(catalogue(Model=model, Frequency='fx', Var='orog', Experiment=wl))
			if (len(orog) > 1): print('Warning: more than one orography file found.  Using first one.')
			return orog[0]

	### You should not get this far, if so then consider extending the whitelist
	print('List of experiments = '+exps)
	raise ValueError('Extend whitelist of Experiments to read orog file from')










# End of cmip5.py