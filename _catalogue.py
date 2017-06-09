import os
import numpy as np
import pandas as pd
import re
import glob, os.path
import iris
import iris.coords as coords
import iris.coord_categorisation
import baspy.util

### Set default dataset
__default_dataset = 'cmip5'

### Setup initial catalogue to be an empty DataFrame
__cached_cat    = pd.DataFrame([]) 

### Define dictionary of cached values
__cached_values         = {} # if not recognised then set to empty dictionary
__cached_cmip5_values   = {'Experiment':['piControl','historical','rcp26','rcp45','rcp85'], 'Frequency':['mon']}
__cached_happi_values   = {'Experiment':['All-Hist','Plus15-Future','Plus20-Future']}
__cached_upscale_values = {}

### Location of personal catologue files
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))

### Set the currently loaded dataset to equal the default
__current_dataset = __default_dataset



def __refresh_shared_catalogue(dataset):
	if dataset == 'cmip5': 
		import baspy.cmip5
		bp.cmip5.__refresh_shared_catalogue()
	if dataset == 'happi': 
		import baspy.happi
		bp.happi.__refresh_shared_catalogue()


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

		print('Filtering catalogue to provide a complete set for variables: ', cat_dict['Var'])

		vals = cat_dict['Var']

		other_keys = cat_dict.keys()
		other_keys.remove('Var')
		for i in other_keys: 
		    if len(cat_dict[i]) > 1:
		        raise ValueError('complete_var_set: only one item allowed for keys other than Var. You have: '+i+'='+str(cat_dict[i]) )

		### Create a new column in catalogue creating strings of unique Model-Run-identifiers
		### i.e., a list of strings with all the useful info in it, e.g., '_MIROC_MIROC5_historical_Amon_v2_mon_atmos_r1i1p1'
		columns = cat.columns.tolist() # list all columns
		columns.remove('Var')  # remove Var and Path columns
		columns.remove('Path') 

		model_run_identifiers = np.array([])
		for index, row in cat.iterrows():
			s = ''
			for c in columns: s = s+'_'+row[c]
			model_run_identifiers = np.append(model_run_identifiers, s)
		cat.loc[:,'Unique_Model_Run_id'] = model_run_identifiers
		print("complete_var_set=True: Adding 'Unique_Model_Run_id' as a new column to the catalgoue")

		### Remove (drop) all items which do not complete a full set of Variables
		for val in vals:
			df0    = cat[ cat['Var'] == vals[0] ]
			df1    = cat[ cat['Var'] == val     ]
			paths0 = np.unique( df0['Unique_Model_Run_id'].values ).tolist()
			paths1 = np.unique( df1['Unique_Model_Run_id'].values ).tolist()
			diff   = set(paths0).symmetric_difference(set(paths1))

			for d in diff: 
				ind = cat[ cat['Unique_Model_Run_id'] == d ].index
				cat = cat.drop(ind, axis=0)

		### Remove temporary column 'Unique_Model_Run_id'
		# cat = cat.drop('Unique_Model_Run_id', axis=1)

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



def catalogue(dataset=None, refresh=None, complete_var_set=False, **kwargs):
	"""
	
	Read whole dataset catalogue for JASMIN (default catalogue is CMIP5)
	   >>> cat = bp.catalogue()

	Read filtered catalogue for JASMIN
	   >>> cat = bp.catalogue(Experiment=['amip','historical'], Var='tas', Frequency=['mon'])
	   
	complete_var_set = True: return a complete set where all Variables are available
	   >>> cat = bp.catalogue(Var=['tas','psl','tasmx'], complete_var_set=True)

	refresh = True: refresh the shared cataloge 
					(the user can then choose to replace their personal catalogue once completed)
					This should only be run when new data has been uploaded into the data archive, 
					or when there has been a change to the items stored within the catalogue
	   >>> cat = bp.catalogue(dataset='cmip5', refresh=True)
	   
	List of catalogued datasets available:
		cmip5, happi, upscale

	"""

	global __cached_cat
	global __cached_values
	global __default_dataset
	global __current_dataset
	global __orig_cached_values

	### First time using specified dataset
	if (dataset != __current_dataset):

		__cached_cat    = pd.DataFrame([])

		if (dataset == None):
			print("Warning: dataset not specified, defaulting to dataset='"+__default_dataset+"'")
			dataset           = __default_dataset

		if dataset == 'cmip5': 
			__cached_values      = __cached_cmip5_values
			__orig_cached_values = __cached_values.copy()

		if dataset == 'happi': 
			__cached_values      = __cached_happi_values
			__orig_cached_values = __cached_values.copy()

		__current_dataset = dataset

	### Set dataset specific variables
	if dataset == 'cmip5': 
		import baspy.cmip5
		cat_file = baspy.cmip5.cat_file
		__shared_cat_file = baspy.cmip5.__shared_cat_file

	if dataset == 'happi':
		import baspy.happi
		cat_file = baspy.happi.cat_file
		__shared_cat_file = baspy.happi.__shared_cat_file

	### Refresh catalogue csv file
	if (refresh == True): 
		__refresh_shared_catalogue(dataset)
		__cached_cat = pd.DataFrame([])

	update_cached_cat = False

	### Read catalgoue for the first time
	if (__cached_cat.size == 0):

		### This is the first time we have run the code, so read and cache catalogue (done below)
		update_cached_cat = True

		### Check to see if there is a newer version of the catalogue available
		if ( os.path.getctime(__shared_cat_file) > os.path.getctime(cat_file) ):
			print('###################################################################')
			print('Note that there is a newer version of the shared catalogue at      ')
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

		if (complete_var_set == True): 
			raise ValueError('Can not specify complete_var_set when less than two variables (Var) are defined')

		### If no user_values are specified then read in default/original list of cached values
		print('No user values defined, will therefore filter catalogue using default values')
		cat = __filter_cat_by_dictionary( __cached_cat, __orig_cached_values )

	return cat








