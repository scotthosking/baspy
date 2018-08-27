import numpy as np
import warnings
import glob, re, os
import pandas as pd
import iris
import iris.coords as coords
import util
from datasets import dataset_dictionaries

##################
### Global values
##################

### Setup initial catalogue to be an empty DataFrame
__cached_cat = []

### If CachedExperiments not defined then set to empty dictionary
__cached_values = {}

### Set the currently loaded dataset to equal the default
from datasets import __default_dataset
__current_dataset = __default_dataset


##################
### Definitions
##################

def setup_catalogue_file(dataset):
    '''
    Define locations of catalogue files, + copy or download if newer files
    available (compared to personal files in ~/.baspy)
    '''

    from baspy.util import get_last_modified_time_from_http_file
    
    copied_new_cat_file = False

    ### 1. define filepaths
    from baspy import __baspy_path, __catalogues_dir, __catalogues_url
    cat_fname    = dataset+'_catalogue.csv'
    cat_file     = __baspy_path+'/'+cat_fname
    __shared_local_cat_file = __catalogues_dir + cat_fname
    __shared_url_cat_file   = __catalogues_url + cat_fname

    ### 2. Setup local baspy folder to store catalogues
    if not os.path.exists(__baspy_path): 
        os.makedirs(os.path.expanduser(__baspy_path))
    
    ### 3. Do we have a catalogue file to work with?
    get_file = False
    if (os.path.isfile(cat_file) == False):    
        print(cat_file+" does not exist, this may be the first time you've requested this catalogue")
        get_file = True

    ### 4. Get catalogue file (if we need to)
    if get_file == True:
        if os.path.exists(__shared_local_cat_file):
            ### We have access to the shared catalogue file
            print('Copying shared catalogue to '+__baspy_path)
            import shutil
            shutil.copy2(__shared_local_cat_file, cat_file)
            copied_new_cat_file = True
        else:
            ### Download file over the internet (slower)
            print('Downloading shared catalogue to '+__baspy_path)
            import urllib
            urllib.urlretrieve (__shared_url_cat_file, cat_file)
            copied_new_cat_file = True

    ### 5. Check whether a newer version of the catalogue is available compared to the one 
    ###            we already have
    newer_available_location = None
    if os.path.exists(__shared_local_cat_file):
        if ( os.path.getmtime(__shared_local_cat_file) > os.path.getmtime(cat_file) ):
            newer_available_location = __shared_local_cat_file
    else:
        from datetime import datetime
        url_file_timestamp = get_last_modified_time_from_http_file(__shared_url_cat_file)
        if ( url_file_timestamp > os.path.getmtime(cat_file) ):
            newer_available_location = __shared_url_cat_file

    if newer_available_location != None:
        warnings.warn('Using catalogue '+cat_file+'. Note that a newer version is available at '+newer_available_location)

    ### 6. If __shared_local_cat_file does not exist then set it to personal file in .baspy
    if os.path.exists(__shared_local_cat_file) == False:
        __shared_local_cat_file = cat_file

    return copied_new_cat_file, cat_file, __shared_local_cat_file








def __refresh_shared_catalogue(dataset):
    '''
    Rebuild the catalogue
    '''

    ### Setup catalogue file (copy over if needs be)
    copied_new_cat_file, cat_file, __shared_cat_file = setup_catalogue_file(dataset)

    if dataset not in dataset_dictionaries.keys():
        raise ValueError("The keyword 'dataset' needs to be set and recognisable in order to refresh catalogue")

    dataset_dict   = dataset_dictionaries[dataset]
    root           = dataset_dict['Root']
    DirStructure   = dataset_dict['DirStructure'].split('/')
    InclExtensions = dataset_dict['InclExtensions']

    ### Get paths for data   
    filewalk = ''
    for D in DirStructure:
        if D.startswith('!'):
            ### fix directory to string after '!'
            filewalk = filewalk + '/' + D[1:]
        else:
            filewalk = filewalk + '/*'

    print('Building '+dataset+' catalogue now...')
    paths = glob.glob(root+filewalk)
    paths = filter(lambda f: os.path.isdir(f), paths)


    ### write data to catalogue (.csv) using a Pandas DataFrame
    rows = []
    n_root_levels = len(dataset_dict['Root'].split('/'))
    for path in paths:

        parts = re.split('/', path)[n_root_levels:]

        # relative_path = '/'.join(parts)

        ### Make list of file names: i.e., 'file1.nc;file2.nc'
        fnames = [fn for fn in os.listdir(path) if any(fn.endswith(ext) for ext in InclExtensions)]
        for fn in fnames:
            if len(fn.split('.')) != 2:
                print('Ignoring '+path+'/'+fn)
                fnames.pop( fnames.index(fn) )
        files_str = ';'.join(fnames)


        ### Only add a row for paths where we have data files
        if len(fnames) > 0:
            start_date, end_date = get_file_date_ranges(fnames, dataset_dict['FilenameStructure'])

            ### Append parts in correct order
            parts.append(int(np.nanmin(start_date)))
            parts.append(int(np.nanmax(end_date)))
            parts.append(path)    
            parts.append(files_str)

            ### Append new row
            rows.append(parts)

    df = pd.DataFrame(rows, columns=DirStructure + ['StartDate', 'EndDate', 'Path','DataFiles'])

    ### save to local dir
    df.to_csv(cat_file, index=False)

    ### Add Root directory as header (Python v2)
    # with file(cat_file, 'r') as original: file_data = original.read()
    # with file(cat_file, 'w') as modified: modified.write("# Root="+root+"\n" + file_data)
    ### Python 3
    # with open(cat_file, 'r') as original: file_data = original.read()
    # with open(cat_file, 'w') as modified: modified.write("# Root="+root+"\n" + file_data)

    if os.path.exists(__shared_cat_file):
        ### We have access to __shared_cat_file
        print('Copying new catalogue to '+__shared_cat_file)
        import shutil
        shutil.copy2(cat_file, __shared_cat_file)





def get_file_date_ranges(fnames, filename_structure):
    ### Get start and end dates from file names
    ind = filename_structure.split('_').index('StartDate-EndDate')
    start_dates, end_dates = np.array([]), np.array([])

    for fname in list(fnames):

        fname = os.path.splitext(fname)[0] # rm extention

        ### Is this file time-varying?
        if '_fx_' in fname:
            ### Fixed variable (e.g., land-mask)
            start_date, end_date = 0, 0

        else:
            ### Time-varying (e.g., temperature)
            date_str = fname.split('_')[ind].split('-')

            ### Interpreting the dates
            if len(date_str) == 2:
                ### e.g.,'19900101-20000101'
                start_date, end_date = int(date_str[0]), int(date_str[1])

            elif (len(date_str) == 3):
                if (date_str[2] == 'clim'):
                    ### e.g.,'186001-187912-clim'
                    ### see /badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/piControl/mon/atmos/Amon/r1i1p1/latest/pfull
                    start_date, end_date = int(date_str[0]+'01'), int(date_str[1]+'31')
                else:
                    print('Cannot identify dates '+fname)

            elif (len(date_str) == 1) & (int(date_str[0]) >= 1800) & (int(date_str[0]) <= 2300):
                ### e.g., '1990'
                ### see /badc/cmip5/data/cmip5/output1/ICHEC/EC-EARTH/amip/subhr/atmos/cfSites/r3i1p1/latest/ccb
                start_date, end_date = int(date_str[0]), int(date_str[0])

            else:
                ### Can't define date
                ###### To do: if no date_range then get from ncdump? !!
                print('Cannot identify dates '+fname)
                start_date, end_date = np.nan, np.nan

        start_dates = np.append( start_dates, start_date )
        end_dates   = np.append( end_dates,   end_date )   

    return start_dates, end_dates




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
        print("complete_var_set=True: Adding 'Unique_Model_Run' as a new column to the catalogue")
        cat['Unique_Model_Run'] = cat['Centre']+'_'+cat['Model']+'_'+cat['RunID'].astype(str)+'_'+cat['Experiment']

        ### Remove (drop) all items which do not complete a full set of Variables
        for val in vals:
            df0    = cat[ cat['Var'] == vals[0] ]
            df1    = cat[ cat['Var'] == val     ]
            paths0 = np.unique( df0['Unique_Model_Run'].values ).tolist()
            paths1 = np.unique( df1['Unique_Model_Run'].values ).tolist()
            diff   = set(paths0).symmetric_difference(set(paths1))

            for d in diff: 
                ind = cat[ cat['Unique_Model_Run'] == d ].index
                cat = cat.drop(ind, axis=0)

        ### Remove temporary column 'Unique_Model_Run'
        # cat = cat.drop('Unique_Model_Run', axis=1)

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













def catalogue(dataset=None, refresh=None, complete_var_set=False, read_everything=False, **kwargs):
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
        cmip5, happi

    """

    global __cached_cat
    global __cached_values
    global __default_dataset
    global __current_dataset
    global __orig_cached_values
    
    update_cached_cat = False

    ### Ensure we have a dataset specified - use default if none specified by user
    if (dataset == None):
        print("Warning: dataset not specified, defaulting to: dataset='"+__default_dataset+"'")
        dataset = __default_dataset

    ### Define cached values for requested catalogue
    __cached_values = dataset_dictionaries[dataset]['Cached']        

    __orig_cached_values = __cached_values.copy()

    ### First time using specified dataset
    if (dataset != __current_dataset):
        update_cached_cat = True
        __current_dataset = dataset

    ### Refresh catalogue csv file (i.e., re-scan dataset directories and rebuild catalogue)
    if (refresh == True): 
        __refresh_shared_catalogue(dataset)
        update_cached_cat = True

    ### Setup catalogue (incl. copying over new files if need to)
    copied_new_cat_file, cat_file, __shared_cat_file = setup_catalogue_file(dataset)
    if (copied_new_cat_file == True): update_cached_cat=True

    ### Read whole catalogue (AND RETURN)
    if read_everything == True:
        from pandas import read_csv
        cat = read_csv(cat_file)
        print(">> Read whole catalogue, any filtering has been ignored <<")
        return cat

    ### Read catalgoue for the first time
    if (type(__cached_cat) == list):    
        update_cached_cat = True

    ### Get user defined filter/dictionary from kwargs
    user_values = kwargs.copy()

    ### Update/expand cached catalogue
    ### Add any additional items from user for only those keys already defined in cached_cat (ignore other keys from user)
    expanded_cached_values = __combine_dictionaries(__cached_values.keys(), __cached_values, user_values)
    compare_dicts          = __compare_dict(expanded_cached_values, __cached_values)
    if (compare_dicts == 'different'): update_cached_cat = True


    if (update_cached_cat == True):
        print('Updating cached catalogue...')
        from pandas import read_csv
        __cached_cat    = read_csv(cat_file)
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
        if 'Var' in user_values.keys():
            for v in np.unique(cat['Var']):
                cat_tmp = cat[ cat['Var'] == v ]
                if (len(np.unique(cat_tmp['SubModel'])) > 1):
                    print('SubModel=', np.unique(cat_tmp['SubModel']))
                    raise ValueError(v+" maybe ambiguous, try defining Submodel (e.g., SubModel='atmos')")

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








