#!/usr/bin/python
# Filename: cmip5.py

import os
import numpy as np
import pandas as pd
import re
import glob, os.path
import iris
import iris.coords as coords
import iris.coord_categorisation
import baspy.util


cat_fname = 'cmip5_catalogue.csv'

### Location of personal catologue file
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))
cat_file = __baspy_path+'/'+cat_fname

### If personal catologue file does not exist then copy shared catologue file
__shared_cat_file = '/group_workspaces/jasmin/bas_climate/data/data_catalogues/'+cat_fname
if (os.path.isfile(cat_file) == False):	
	print("Catalogue of CMIP5 data does not exist, this may be the first time you've run this code")
	print('Copying shared catalogue to '+__baspy_path)
	import shutil
	shutil.copy2(__shared_cat_file, cat_file)

### Directories
cmip5_dir = '/badc/cmip5/data/cmip5/output1/'

### Originally set cat to an empty DataFrame
__cached_cat    = pd.DataFrame([])
__cached_values = {'Experiment':['piControl','historical','rcp26','rcp45','rcp85'], 'Frequency':['mon']}
__orig_cached_values = __cached_values.copy()


def __refresh_shared_catalogue():
	'''
	Rebuild the CMIP5 catalogue
	'''

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

	    ### Add Version to catalogue and Path
	    real_path = os.path.realpath(dir)
	    version   = re.split('/',real_path)[-2]
	    parts.append(version)
	    a = re.split('/', dir)
	    a[-2] = version
	    dir = '/'.join(a)

	    parts.append(dir)        
	    rows.append(parts)

	df = pd.DataFrame(rows, columns=['Centre','Model','Experiment','Frequency','SubModel','CMOR','RunID','Var','Version','Path'])

	### save to local dir
	df.to_csv(__shared_cat_file, index=False)




def __combine_dictionaries(keys, dict1_in, dict2_in):

	'''
	Combine dictionaries for only those specified keys
	'''
 
	dict1 = dict1_in.copy()
	dict2 = dict2_in.copy()

	for key in keys:

		### if key not defined in dictionaries then add an empty key (e.g., {'Model':[]})
		if key not in dict1.keys(): dict1.update({key:[]})
		if key not in dict2.keys(): dict2.update({key:[]})

		### If not already, convert list
		if (dict1[key].__class__ == str):        dict1[key] = [dict1[key]]
		if (dict1[key].__class__ == np.string_): dict1[key] = [dict1[key]]
		if (dict2[key].__class__ == str):        dict2[key] = [dict2[key]]
		if (dict2[key].__class__ == np.string_): dict2[key] = [dict2[key]]

		### combine dictionaries (add dict2 to dict1) and
		### remove duplicated items from within a key's list 
		###     e.g, Var=['tas','tas','va'] --> Var=['tas','va']
		dict1[key] = list( set(dict1[key] + dict2[key]) )

		### if a dict key has size 0 (no items) then remove it from dict
		if len(dict1[key]) == 0: del dict1[key]

	return dict1



def __filter_cat_by_dictionary(cat, cat_dict, complete_var_set=False):

	keys = cat_dict.keys()

	### Filter catalogue
	for key in keys:

		### Ensure that values within a key are defined as a list
		if (cat_dict[key].__class__ == str):        cat_dict[key] = [cat_dict[key]]
		if (cat_dict[key].__class__ == np.string_): cat_dict[key] = [cat_dict[key]]

		vals      = cat_dict[key]
		cat_bool  = np.zeros(len(cat), dtype=bool)
		uniq_vals = np.unique(cat[key])

		for val in vals:
			if (val not in uniq_vals): 
				print('Are you sure that data exists that satisfy all your constraints?')
				raise ValueError(val+' not found. See available in current catalouge: '+np.array_str(uniq_vals) )
			cat_bool = np.add( cat_bool, (cat[key] == val) )

		### Apply filter 	
		cat = cat[cat_bool]


	### "2nd Pass" keep only items where all Variables are available for that Model/Experiment/RunID/Frequency etc
	if (complete_var_set == True):

	    if ('Var' not in keys):
	        raise ValueError('Two or more Varaibles (Var=) need to be specified in order to use complete_var_set')
	    if (len(cat_dict['Var']) < 2):
	        raise ValueError('Two or more Varaibles (Var=) need to be specified in order to use complete_var_set')


	    vals = cat_dict['Var']

	    other_keys = cat_dict.keys()
	    other_keys.remove('Var')
	    for i in other_keys: 
	        if len(cat_dict[i]) > 1:
	            raise ValueError('complete_var_set: only one item allowed for keys other than Var. You have: '+i+'='+str(cat_dict[i]) )

		### Create a new column in catalogue, same as 'Path' but with the trailing (Var) directory removed
		path_head = np.array([])
		for path in cat['Path'].values:
			path_head = np.append(path_head, os.path.split(path)[0])
		cat.loc[:,'Path_head'] = path_head

		### Remove (drop) all items which do not complete a full set of Variables
		for val in vals:
			df0    = cat[ cat['Var'] == vals[0] ]
			df1    = cat[ cat['Var'] == val     ]
			paths0 = np.unique( df0['Path_head'].values ).tolist()
			paths1 = np.unique( df1['Path_head'].values ).tolist()
			diff   = set(paths0).symmetric_difference(set(paths1))

			for d in diff: 
				ind = cat[ cat['Path_head'] == d ].index
				cat = cat.drop(ind, axis=0)

		### Remove temporary column 'Path_head'
		cat = cat.drop('Path_head', axis=1)

	### Return a filtered catalogue
	return cat




def __compare_dict(dict1_in, dict2_in):

	dict1 = dict1_in.copy()
	dict2 = dict2_in.copy()
	compare_dicts = 'same'
	uniq_keys = list( set(dict1.keys() + dict2.keys()) )

	for key in uniq_keys:

		### if key not defined in dictionaries then add an empty key (e.g., {'Model':[]})
		if key not in dict1.keys(): dict1.update({key:[]})
		if key not in dict2.keys(): dict2.update({key:[]})

		### convert string to list 
		if (type(dict1[key]) == str): dict1[key] = [dict1[key]]
		if (type(dict2[key]) == str): dict2[key] = [dict2[key]]
		
		### remove duplicated items from within a key's list
		###     e.g, Var=['tas','tas','va'] --> Var=['tas','va']
		dict1[key] = list(set(dict1[key]))
		dict2[key] = list(set(dict2[key]))

		### Sort key list
		dict1[key].sort()
		dict2[key].sort()

		if dict1[key] != dict2[key]: compare_dicts = 'different'

	return compare_dicts



def catalogue(refresh=None, complete_var_set=False, **kwargs):
	"""
	
	Read whole CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue()

	Read filtered CMIP5 catalogue for JASMIN
	   >>> cat = cmip5_catalogue(Experiment=['amip','historical'], Var='tas', Frequency=['mon'])
	   
	complete_var_set = True: return a complete set where all Variables are available
	   >>> cat = cmip5_catalogue(Var=['tas','psl','tasmx'], complete_var_set=True)

	refresh = True: refresh the shared CMIP5 cataloge 
					(the user can then choose to replace their personal catalogue once completed)
					This should only be run when new data has been uploaded into the data archive, 
					or when there has been a change to the items stored within the catalogue
	   >>> cat = cmip5_catalogue(refresh=True)
	   

	"""

	### Build a new catalogue
	if (refresh == True): __refresh_shared_catalogue()

	global __cached_cat
	global __cached_values

	update_cached_cat = False

	### Read catalgoue for the first time
	if (__cached_cat.size == 0):

		### This is the first time we have run the code, so read and cache catalogue (done below)
		update_cached_cat = True

		### Check to see if there is a newer version of the catalogue available
		if ( os.path.getctime(__shared_cat_file) > os.path.getctime(cat_file) ):
			print('###################################################################')
			print('Note that there is a newer version of the shared CMIP5 catalogue at')
			print(__shared_cat_file)
			print('For now you will continue to use the one in your personal directory')
			print(__baspy_path+'/.')
			print('###################################################################')


	### Get user defined filter/dictionary from kwargs
	user_values = kwargs.copy()

	### Update/expand cached catalogue
	### Add any additional items from user for only those keys already defined in cached_cat (ignore other keys from user)
	expanded_cached_values = __combine_dictionaries(__cached_values.keys(), __cached_values, user_values)
	compare_dicts          = __compare_dict(expanded_cached_values, __cached_values)
	if (compare_dicts == 'different'): update_cached_cat = True


	if (update_cached_cat == True):
		print('Updating cached catalogue...') 
		__cached_cat    = pd.read_csv(cat_file)
		__cached_values = expanded_cached_values.copy()
		__cached_cat    = __filter_cat_by_dictionary( __cached_cat, __cached_values )
		print('>> Current cached values from catalogue (this can be extended by specifying additional values) <<')
		print(__cached_values)
		print('')


	if user_values != {}:

		### Produce the catalogue for user
		cat = __filter_cat_by_dictionary( __cached_cat, user_values, complete_var_set=complete_var_set )

		# Some Var names are duplicated across SubModels (e.g., Var='pr')
		# Force code to fall over if we spot more than one unique SubModel
		# when Var has been set.
		if (len(np.unique(cat['SubModel'])) > 1) & ('Var' in user_values.keys()):
			print('SubModel=', np.unique(cat['SubModel']))
			raise ValueError("Var maybe ambiguous, try defining Submodel (e.g., SubModel='atmos')")

		### We do not want a cube with multiple Frequencies (e.g., monthly and 6-hourly)
		if (len(np.unique(cat['Frequency'])) > 1):
			print('Frequency=', np.unique(cat['Frequency']))
			raise ValueError("Multiple time Frequencies present in catalogue, try defining Frequency (e.g., Frequency='mon')")

	else:

		### If no user_values are specified then read in default/original list of cached values
		print('No user values defined, will therefore filter catalogue using default values')
		cat = __filter_cat_by_dictionary( __cached_cat, __orig_cached_values )

	return cat
















def get_template_cube():
	'''
	Get a cube to use as a CMIP5 template
	'''
	cat  = catalogue(Model='CMCC-CM',Experiment='historical',Var='tas',Frequency='mon')
	con  = iris.Constraint(cube_func=lambda cube: cube.var_name == 'tas') & iris.Constraint(year=2000) & iris.Constraint(month=1)
	cube = get_cubes(cat.iloc[[0]], constraints=con)
	return cube[0]




def callback(cube, field, filename):
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

	### Add additional time coordinate categorisations
	if (len(cube.coords(axis='t')) > 0):

		time_name = cube.coord(axis='t').var_name

		iris.coord_categorisation.add_year(cube, time_name, name='year')
		iris.coord_categorisation.add_month_number(cube, time_name, name='month')

		### Add season
		seasons = ['djf', 'mam', 'jja', 'son']
		iris.coord_categorisation.add_season(cube, time_name,      name='clim_season', seasons=seasons)
		iris.coord_categorisation.add_season_year(cube, time_name, name='season_year', seasons=seasons)



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
			count = count+1
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
					
			if any([run_id not in nc, nc.endswith('.nc4')]): ### Note, this causes an issue in happi.get_cubes (generalise!!)
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
			
			cube = iris.load(dirfilename, callback=callback,
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
		cubelist1 = baspy.util.rm_time_overlaps(cubelist1)

		### Unify lat-lon grid
		#cubelist1 = baspy.util.util.unify_grid_coords(cubelist1, cubelist1[0])
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Create a cubelist from cubes
		cubelist2.extend([cube])

	return cubelist2



def get_cube(filt_cat, constraints=None, verbose=True):

	if (len(filt_cat.index) == 1): 
		cube = get_cubes(filt_cat, constraints=constraints, verbose=verbose)
		cube = cube[0]

	if (len(filt_cat) > 1): 
		raise ValueError("Error: more than one cube present.  Try 'get_cubes' instead")
	if (len(filt_cat) == 0): 
		raise ValueError("Error: no cubes specified in catalogue.")

	return cube





def get_fx(model, Var):

	### substitute var (e.g., Orography) for models where file is missing
	### with models with the same orography --- CHECK THESE ARE SAME RESOLUTION!!!!!
	if (model == 'HadGEM2-AO'): model = 'HadGEM2-CC'

	filt_cat = catalogue(Model=model, Frequency='fx', Var=Var)
	exps     = filt_cat['Experiment'].values

	if (len(exps) == 0): raise ValueError('No '+Var+' files exists for '+model)

	### whitelist experiments to read data from (ordered list)
	whitelist = ['historical', 'piControl', 'amip', 'rcp45', 'decadal1980']

	for wl in whitelist:
		if (wl in exps): 
			fx = get_cubes(catalogue(Model=model, Frequency='fx', Var=Var, Experiment=wl))
			if (len(fx) > 1): print('Warning: more than one '+Var+' file found.  Using first one.')
			return fx[0]

	### You should not get this far, if so then consider extending the whitelist
	print('List of experiments = '+exps)
	raise ValueError('Extend whitelist of Experiments to read '+Var+' file from')

def get_orog(model):
	'''
	Get Orography for model
		>>> orog = get_orog('HadCM3')
	'''
	return get_fx(model, 'orog')


def get_laf(model):
	return get_fx(model, 'sftlf')




# End of cmip5.py