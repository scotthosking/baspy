import numpy as np
import warnings
import glob, os
import pandas as pd
from .datasets import dataset_dictionaries, __default_dataset
import requests

##################
### Global values
##################

### Setup initial catalogue to be an empty DataFrame
__cached_cat = []

### If CachedExperiments not defined then set to empty dictionary
__cached_values = {}

### Set the currently loaded dataset to equal the default
__current_dataset = __default_dataset

### This is used to ensure the catalogue files are compatible 
### with this version of the code. Update this number if any changes are
### made to the way the way we read/write the catalogues and force 
### the file to be updated
__catalogue_version = 20190816




##################
### Definitions
##################

def setup_catalogue_file(dataset):
    '''
    Define locations of catalogue files, + copy or download if newer files
    available (compared to personal files in ~/.baspy)
    '''

    from .util import get_last_modified_time_from_http_file
    
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

    ### 4. no trace of catalogue file, lets build one
    requests.get(__shared_url_cat_file, timeout=20) # check we have connection - stops the users terminal hanging...

    force_catalogue_refresh = False
    if (requests.get(__shared_url_cat_file).status_code == 404) & \
            (os.path.isfile(cat_file) == False):
        force_catalogue_refresh = True
    
    ### 5. Get catalogue file (if we need to)
    if get_file == True:
        if os.path.exists(__shared_local_cat_file):
            ### We have access to the shared catalogue file
            print('Copying shared catalogue to '+__baspy_path)
            import shutil
            shutil.copy2(__shared_local_cat_file, cat_file)
            copied_new_cat_file = True
        elif (requests.get(__shared_url_cat_file).status_code == 200):
            ### Download file over the internet (slower)
            print('Downloading shared catalogue to '+__baspy_path)
            r = requests.get(__shared_url_cat_file)
            with open(cat_file, 'wb') as f:  
                f.write(r.content)
            copied_new_cat_file = True
        else:
            pass

    ### 6. Check whether a newer version of the catalogue is available compared to the one 
    ###            we already have
    newer_available_location = None
    if os.path.exists(__shared_local_cat_file):
        if ( os.path.getmtime(__shared_local_cat_file) > os.path.getmtime(cat_file) ):
            newer_available_location = __shared_local_cat_file
    else:
        from datetime import datetime
        url_file_timestamp = get_last_modified_time_from_http_file(__shared_url_cat_file)
        if os.path.exists(cat_file):
            if ( url_file_timestamp > os.path.getmtime(cat_file) ):
                newer_available_location = __shared_url_cat_file

    if newer_available_location != None:
        warnings.warn('Using catalogue '+cat_file+'. Note that a newer version is available at '+newer_available_location)

    return force_catalogue_refresh, copied_new_cat_file, cat_file, __shared_local_cat_file





def write_csv_with_comments(df, fname, **kwargs):

  global __catalogue_version
    
  user_values = kwargs.copy()
  user_values.update({'catalogue_version':__catalogue_version})
  keys   = list(user_values.keys())
  values = list(user_values.values())
  if 'root' in keys:
    df['Path'] = df['Path'].map(lambda x: x.replace(user_values['root'], ''))

  with open(fname, 'w') as file:
      for key, value in zip(keys,values):
        comment = '# '+str(key)+'='+str(value)+'\n'
        file.write(comment)
      df = df.drop_duplicates()
      df.to_csv(file, index=False)



def read_csv_with_comments(fname):
  
  global __catalogue_version

  ### read file
  from pandas import read_csv
  metadata = {}
  with open(fname) as fp:  
      line = fp.readline()
      while line.startswith('#'):
         # takes elements from comment and add to dictionary
         elements=line.strip().replace('#','').replace(' ','').split('=')
         metadata.update({elements[0]:elements[1]})
         ### read next line
         line = fp.readline()

  df = read_csv(fname, comment='#') # define dtypes here to reduce memory usage (see df.memory_usage() and df.dtypes())!
  df['dataset'] = metadata['dataset']
  df = df.astype({'dataset':'category'}) # can we do this in one step to limit initial memory usage from line above? (see df.memory_usage())

  if __catalogue_version > int(metadata['catalogue_version']):
    raise ValueError('Your catalogue needs to be updated to work with this version of the code')

  return df



def __refresh_shared_catalogue(dataset):
    '''
    Rebuild the catalogue
    '''

    ### Setup catalogue file (copy over if needs be)
    force_catalogue_refresh, copied_new_cat_file, cat_file, __shared_cat_file = setup_catalogue_file(dataset)

    if dataset not in dataset_dictionaries.keys():
        raise ValueError("The keyword 'dataset' needs to be set and recognisable in order to refresh catalogue")

    dataset_dict   = dataset_dictionaries[dataset]
    root           = dataset_dict['Root']
    DirStructure   = dataset_dict['DirStructure'].split('/')
    InclExtensions = dataset_dict['InclExtensions']

    ### Get paths for data   
    filewalk = ''
    for i, D in enumerate(DirStructure):
        if '!' in D:
            ### fix directory to part of string after '!'
            filewalk = filewalk + '/' + D.split('!')[1]
            ### remove trailing !XXXX from string
            DirStructure[i] = D.split('!')[0]
        else:
            filewalk = filewalk + '/*'

    print('Building '+dataset+' catalogue now...')
    paths = glob.glob(root+filewalk)
    paths = filter(lambda f: os.path.isdir(f), paths)

    ### write data to catalogue (.csv) using a Pandas DataFrame
    rows = []
    n_root_levels = len(dataset_dict['Root'].split('/'))
    for path in paths:

        ### Update 'path' by turning all symlinks linked to a folder in 
        ###    the same directory into its real location
        ### e.g., for cmip5, Version: latest --> v20120709
        parts = path.split('/')
        for i in range(n_root_levels, len(parts)+1):
            if os.path.islink('/'.join(parts[0:i])):
                realpath = os.readlink('/'.join(parts[0:i]))
                if len(realpath.split('/')) == 1:
                    ### i.e., symlink is linked to folder in same dir
                    path = '/'.join(parts[0:i-1]) + '/' + \
                            realpath + '/' + \
                            '/'.join(parts[i:])

        ### Now use updated 'path' to create catalogue
        parts = path.split('/')[n_root_levels:]
        if '' in parts: parts.remove('')

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
    #df.to_csv(cat_file, index=False)
    write_csv_with_comments(df, cat_file, dataset=dataset, root=root)

    if os.path.exists('/'.join(__shared_cat_file.split('/')[:-1])):
        ### We have access to __shared_cat_file
        print('Copying new catalogue to '+__shared_cat_file)
        if cat_file != __shared_cat_file:
            import shutil
            shutil.copy2(cat_file, __shared_cat_file)





def get_file_date_ranges(fnames, filename_structure):
    ### Get start and end dates from file names
    ind = filename_structure.split('_').index('StartDate-EndDate')
    start_dates, end_dates = np.array([]), np.array([])

    for fname in list(fnames):

        fname = os.path.splitext(fname)[0] # rm extention

        ### Is this file time-varying?
        if ('_fx_' in fname) | ('_Efx_' in fname) | ('_Ofx_' in fname):
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


def __create_unique_run_identifer(catlg, col_name):
    dataset = catlg['dataset'].iloc[0]
    dataset_dict = dataset_dictionaries[dataset]
    my_list = dataset_dict['DirStructure'].replace('Var','').split('/')
    my_list.remove('')
    
    my_command = ''
    for l in my_list: my_command = my_command + "catlg['" +l+ "']+'-'+"
        
    catlg[col_name] = eval(my_command[0:-5])
    
    return catlg



def __complete_var_set(catlg, filt_dict):
    '''
    Ensure we have a complete set of variables 
    for each model-run-version
    '''
    
    if 'Var' not in filt_dict.keys(): 
        return catlg

    Vars  = filt_dict['Var']
    nVars = len(Vars)

    if (nVars == 1): return catlg

    print('More than one Var specified, return rows where we ' + \
            'have a complete set of variables for each '     + \
            'unique run \n')

    # create unique identifier for each unique run (generalise!!!)
    catlg = __create_unique_run_identifer(catlg,'Unique_Model_Run')

    # number of Vars in each model-run-version group
    catlg_gp = catlg.groupby(['Unique_Model_Run']).count().max(axis=1)

    # select groups where we have the correct number of variables 
    catlg_gp = catlg_gp[ catlg_gp == nVars ]

    # filter whole catalogue
    catlg = catlg[ catlg.isin({'Unique_Model_Run':catlg_gp.index}
                                )['Unique_Model_Run'] == True ]

    if len(catlg) == 0:
        raise ValueError('There are no rows where all specified Vars exist for Model-RunID-Version',
                             filt_dict['Var'])

    return catlg



def __filter_cat_by_dictionary(catlg, cat_dict):
    '''
    Get rows which match cat_dict
    '''
    keys  = cat_dict.keys() 
    nkeys = len(keys)

    for key in keys:

        ### Ensure that values within a key are defined as a list
        if (cat_dict[key].__class__ == str):        cat_dict[key] = [cat_dict[key]]
        if (cat_dict[key].__class__ == np.string_): cat_dict[key] = [cat_dict[key]]

        vals      = cat_dict[key]
        uniq_vals = np.unique(catlg[key])

        for val in vals:
            if (val not in uniq_vals): 
                print('Are you sure that data exists that satisfy all your constraints?')
                raise ValueError(val+' not found. See available in current catalouge: ' \
                                    +np.array_str(uniq_vals) )

    a     = catlg.isin(cat_dict)
    catlg = catlg[ (a.sum(axis=1) == nkeys) ]
    catlg = __complete_var_set(catlg, cat_dict)

    return catlg




def __compare_dict(dict1_in, dict2_in):

    dict1 = dict1_in.copy()
    dict2 = dict2_in.copy()
    compare_dicts = 'same'
    
    # uniq_keys = list( set(dict1.keys() + dict2.keys() ) )    # python2 only
    uniq_keys = list( set(dict1.keys()) | set(dict2.keys()) )  # python2+3

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













def catalogue(dataset=None, refresh=None, read_everything=False, **kwargs):
    """
    
    Read whole dataset catalogue for JASMIN (default: dataset='cmip5')
       >>> catlg = bp.catalogue(dataset='cmip6')

    Look at the first row to get a feel for the catologue layout
       >>> print(catlg.iloc[0])

    Read filtered catalogue for JASMIN (
    (Note to help with filtering, you can use any CASE for kwargs + some common shortened words (freq, exp, run) )
       >>> cat = bp.catalogue(dataset='cmip5', experiment=['amip','historical'], var='tas', frequency=['mon'])

    refresh = True: refresh the shared cataloge 
    This should only be run when new data has been uploaded into the data archive
       >>> cat = bp.catalogue(dataset='cmip5', refresh=True)

    read_everything = True
    By default, bp.catalogue only stores those items defined by 'Cached' within dataset_dictionaries (see datasets.py) 
    This option by-passes that and reads the whole catalogue (which could be very large!)

    """

    global __cached_cat
    global __cached_values
    global __default_dataset
    global __current_dataset
    global __orig_cached_values
    
    # need to check that all kwargs.keys are available in dataset !!!

    update_cached_cat = False

    ### Ensure we have a dataset specified - use default if none specified by user
    if (dataset == None):
        print("Warning: dataset not specified, defaulting to: dataset='"+__default_dataset+"'")
        dataset = __default_dataset

    if dataset not in dataset_dictionaries.keys():
        raise ValueError(dataset+' dataset not currently available: '+str(dataset_dictionaries.keys())+ \
                            '. \n You can add new datasets within dataset.py')

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
    force_catalogue_refresh, copied_new_cat_file, cat_file, __shared_cat_file = setup_catalogue_file(dataset)
    if (copied_new_cat_file == True): update_cached_cat=True
    if (force_catalogue_refresh == True):
        __refresh_shared_catalogue(dataset)
        update_cached_cat = True

    ### Read whole catalogue (AND RETURN)
    if read_everything == True:
        cat = read_csv_with_comments(cat_file)
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


    # ### Edit user keys if they exist but using a different case or shortened
    # for key in user_values.keys():

    #     ### rename keys if using wrong case
    #     lower_keys = [x.lower() for x in __cached_cat.columns]
    #     if (key.lower() in lower_keys) & (key not in __cached_cat.columns):
    #         new_key = __cached_cat.columns[lower_keys.index(key.lower())]
    #         user_values = { k.replace(key,new_key): v for k, v in user_values.items() }

    #     ### Convert some commonly used shortened words
    #     if (key.lower() == 'exp') & ('Experiment' in __cached_cat.columns):
    #         user_values = { k.replace('exp','Experiment'): v for k, v in user_values.items() }
    #     if (key.lower() == 'run') & ('RunID' in __cached_cat.columns):
    #         user_values = { k.replace('run','RunID'): v for k, v in user_values.items() }
    #     if (key.lower() == 'freq') & ('Frequency' in __cached_cat.columns):
    #         user_values = { k.replace('freq','Frequency'): v for k, v in user_values.items() }

    # for key in user_values.keys():
    #     ### key is unknown
    #     if key.lower() not in lower_keys:
    #         avail_columns = __cached_cat.columns.tolist()
    #         avail_columns.remove('Path')
    #         avail_columns.remove('DataFiles')      
    #         raise ValueError("'"+key+"' is not in list of known identifiers: "+str(avail_columns))



    if (update_cached_cat == True):
        print('Updating cached catalogue...')
        __cached_cat    = read_csv_with_comments(cat_file)
        __cached_values = expanded_cached_values.copy()
        __cached_cat    = __filter_cat_by_dictionary( __cached_cat, __cached_values )
        if __cached_values != {}:
            print('>> Current cached values (can be extended by specifying additional values or by setting read_everything=True) <<')
            print(__cached_values)
            print('')


    if user_values != {}:

        ### Produce the catalogue for user
        cat = __filter_cat_by_dictionary( __cached_cat, user_values )

        # Some Var names are duplicated across SubModels (e.g., Var='pr')
        # Force code to fall over if we spot more than one unique SubModel
        # when Var has been set.
        if 'SubModel' in cat.columns:
            if 'Var' in user_values.keys():
                for v in np.unique(cat['Var']):
                    cat_tmp = cat[ cat['Var'] == v ]
                    if (len(np.unique(cat_tmp['SubModel'])) > 1):
                        raise ValueError("Var='"+v+"' maybe ambiguous, try defining Submodel"+ \
                                            "\n SubModel values available: "+str(np.unique(cat_tmp['SubModel'])))

        ### We do not want a list which contains a mixture of Frequencies or CMOR (e.g., monthly and 6-hourly)
        if 'Frequency' in cat.columns:
            if (len(np.unique(cat['Frequency'])) > 1):
                raise ValueError("Multiple time Frequencies present in catalogue, try defining Frequency"+ \
                                    "\n Frequency values available: "+str(np.unique(cat['Frequency'])))
        if 'CMOR' in cat.columns:
            if (len(np.unique(cat['CMOR'])) > 1):
                raise ValueError("Multiple CMOR values present in catalogue, try defining CMOR"+ \
                                   "\n CMOR values available: "+str(np.unique(cat['CMOR'])) )

    else:

        ### If no user_values are specified then read in default/original list of cached values

        if __cached_values == {}:
            print('No user values defined, retrieving whole catalogue')
        else:
            print('No user values defined, will therefore filter catalogue using default values')

        cat = __filter_cat_by_dictionary(__cached_cat, __orig_cached_values)

    return cat





def get_files(df):

    if ('Series' in str(type(df))):
        df = pd.DataFrame([df.values], columns=df.keys())

    ### sanity checks
    if 'DataFrame' not in str(type(df)):
        raise ValueError('Not a DataFrame')

    if len(df) != 1:
        raise ValueError('DataFrame should only have one row. e.g., df.iloc[i]')

    dataset        = df['dataset'].iloc[0]
    dataset_dict   = dataset_dictionaries[dataset]
    root           = dataset_dict['Root']

    directory = root+df['Path'].values[0]+'/'.replace('//','/')
    files     = df['DataFiles'].values[0].split(';')
    files     = [ directory+f for f in files ]

    list_file_extensions = [file.split('.')[-1] for file in files]
    if len(np.unique(list_file_extensions)) > 1:
        # Should we automatically select which extension to use?? (i.e., .nc vs .nc4)
        raise ValueError('>> WARNING: Multiple file extensions present in '+directory+' <<')

    return files
