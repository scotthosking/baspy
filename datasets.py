


### Set default dataset
__default_dataset = 'cmip5'



'''
Define information for each dataset to be indexed and used

    Standard elements (case sensitive):
        * 'Centre', 'Model', Var, Frequency, Experiment, CMOR, Version (i.e., data version), 
                RunID, StartDate-EndDate

    Notes:
    ../!latest/... means only use the 'latest' directory (and ignore sister directories)
        during the filewalk (i.e, default is to use the '*' wildcard)


'''

dataset_dictionaries = \
    { 

    'happi': 
    {'Root':'/group_workspaces/jasmin4/bas_climate/data/happi',
    'DirStructure':'Raw_Derived/Centre/Model/Experiment/CMOR/Version/Frequency/SubModel/Var/RunID',
    'FilenameStructure':'Var_Frequency_Model_Experiment_CMOR_Version_RunID_StartDate-EndDate',
    'InclExtensions':['.nc', '.nc4'],
    'Cached':{'Experiment':['All-Hist','Plus15-Future','Plus20-Future']}},

    'cmip5': 
    {'Root':'/badc/cmip5/data/cmip5/output1',
    'DirStructure':'Centre/Model/Experiment/Frequency/SubModel/CMOR/RunID/!latest/Var',
    'FilenameStructure':'',
    'InclExtensions':['.nc', '.nc4'],
    'Cached': {'Experiment':['piControl','historical','rcp26','rcp45','rcp85'], 'Frequency':['mon']}}
    
    }
