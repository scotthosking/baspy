import re
from pandas.core.series import Series
from pandas import DataFrame
from baspy.datasets import dataset_dictionaries
import iris
import iris.coords as coords
from baspy._iris.util import rm_time_overlaps, unify_similar_grid_coords
from cube_fixes import fix_cubelist_before_concat
import numpy as np

### this will be updated as get_cubes is run
__current_dataset = ''



def callback(cube, field, filename):
    """
    Adds useful auxillary coordinates to the cube

    """

    global __current_dataset

    filename  = re.split('/',filename)[-1]
    split_str = re.split('_',filename)

    filename_strucuture = dataset_dictionaries[__current_dataset]['FilenameStructure']
    long_names = filename_strucuture.split('_')

    whitelist_auxcoords = ['Experiment', 'Model', 'RunID']

    for i in range(0, len(split_str)):
        if long_names[i] in whitelist_auxcoords:
            new_coord = coords.AuxCoord(split_str[i], long_name=long_names[i], units='no_unit')
            cube.add_aux_coord(new_coord)

    ### Add additional time coordinate categorisations
    if (len(cube.coords(axis='t')) > 0):
        time_name = cube.coord(axis='t').var_name
        iris.coord_categorisation.add_year(cube, time_name, name='year')
        iris.coord_categorisation.add_month_number(cube, time_name, name='month')
        seasons = ['djf', 'mam', 'jja', 'son']
        iris.coord_categorisation.add_season(cube, time_name, name='clim_season', seasons=seasons)
        iris.coord_categorisation.add_season_year(cube, time_name, name='season_year', seasons=seasons)




def get_cubes(filt_cat, constraints=None, verbose=True, nearest_lat_lon=False):
    """
    Use filtered catalogue to read files and return a CubeList

    >>> catlg    = bp.catalogue(dataset='cmip5', Experiment='historical', Frequency='mon', Var='psl')
    >>> cubelist = bp.get_cubes(catlg)
    """

    global __current_dataset

    ### Convert Pandas Series to DataFrame
    if 'pandas.core.series.Series' in str(type(filt_cat)):
        filt_cat = DataFrame([filt_cat.values], columns=filt_cat.keys() )

    ### Identify dataset and use defined information
    ### to know how to interpret the directory + filename structures
    datasets = dataset_dictionaries.keys()
    for dataset in datasets:
        if dataset in filt_cat['Path'].values[0]:
            __current_dataset = dataset
    dataset_dict  = dataset_dictionaries[__current_dataset]
    DirStructure  = dataset_dict['DirStructure'].split('/')
    n_root_levels = len(dataset_dict['Root'].split('/'))

    ### start with empty cubelist, then expand within loop
    final_cubelist = iris.cube.CubeList([])
    count = 0
    len_filt = len(filt_cat.index)

    for index, row in filt_cat.iterrows():

        path      = row['Path']
        parts     = re.split('/', path)[n_root_levels:]
        datafiles = re.split(';', row['DataFiles'] )
        var       = parts[ DirStructure.index('Var')        ]
        freq      = parts[ DirStructure.index('Frequency')  ]
        model     = parts[ DirStructure.index('Model')      ]
        run_id    = parts[ DirStructure.index('RunID')      ]
        exp       = parts[ DirStructure.index('Experiment') ]
        centre    = parts[ DirStructure.index('Centre')     ]

        ### Print progress to screen
        if (verbose == True): 
            count = count+1
            print('['+str(count)+'/'+str(len_filt)+'] '+__current_dataset+' '+centre+ \
                                                ' '+model+' '+run_id+' '+exp+' '+var)


        '''
        Sanity checks
        '''
        ### Check that filenames represent what we requested
        for d in datafiles:
            if (model not in d) | (var not in d) | (run_id not in d) | (exp not in d):
                raise ValueError('>> WARNING: Detected misplaced files in '+path+' <<')

        ### Make sure we only use files with the same file extension.
        ### This will likely require us to setup some rules (I remember seeing that CMIP5 EC-Earth has .nc & .nc4)
        list_file_extensions = [dfile.split('.')[-1] for dfile in datafiles]
        if len(np.unique(list_file_extensions)) > 1:
            raise ValueError('>> WARNING: Multiple file extensions present in '+path+' <<')



        ### List only those file names that appear to be within our date-range
        # if (start_date != None) | (end_date != None):
        #     file_date_range = get_cmip_file_date_ranges(datafiles)
        #     if (start_date == None): start_date = np.min(file_date_range[0])
        #     if (end_date == None):   end_date   = np.max(file_date_range[1])

        #     keep_ind1 = np.where( (end_date >= file_date_range[0])   & (end_date <= file_date_range[1])   )[0]
        #     keep_ind2 = np.where( (start_date >= file_date_range[0]) & (start_date <= file_date_range[1]) )[0]
        #     keep_ind  = np.sort(np.unique(np.append(keep_ind1,keep_ind2)))
            
        #     if (len(keep_ind) == 0): 
        #         raise ValueError("No netcdf files within requested date range")
        #     else:
        #         datafiles = datafiles[keep_ind]

        # if type(datafiles) == str: datafiles=[datafiles]
        
        # print datafiles # TMP!!!


        ### Read data with callback to add Experiment (Run) ID to 
        ### distinguish between ensemble memebers
        tmp_cubelist = iris.cube.CubeList([])
        for j in datafiles:
            
            dirfilename = path+'/'+j

            ### contraint by var_name
            con = iris.Constraint(cube_func=lambda cube: cube.var_name == var)
            
            ### Add user defined constrains (e.g., level, time)
            if (constraints != None): con = con & constraints
            
            ### Load single file
            cube = iris.load(dirfilename, callback=callback, constraints=con)
            if (len(cube) > 1): raise ValueError('more than one cube loaded, expected only one!')

            if ( ('iris.cube.CubeList' in str(type(cube))) & (len(cube) == 1) ):    
                cube = cube[0]
            
                if nearest_lat_lon != False:
                    ### nearest_lat_lon = [('latitude', YYY), ('longitude', XXX)]
                    cube = cube.interpolate( nearest_lat_lon, iris.analysis.Nearest() )

                ### Remove attributes to enable cubes to concatenate
                cube.attributes.clear() ### To do - keep/unify attributes!!!
                
                ### Create cubelist from cubes
                tmp_cubelist.extend([cube])

        ### Change reference time of cubes so times match in order to 
        ### encourage cubes to concatenate
        iris.util.unify_time_units(tmp_cubelist)
        
        ### Remove temporal overlaps
        tmp_cubelist = rm_time_overlaps(tmp_cubelist)

        ### Unify lat-lon grid
        tmp_cubelist = unify_similar_grid_coords(tmp_cubelist, tmp_cubelist[0])
        
        ### Apply Fixes to enable cubes in tmp_cubelist to concatenate ###
        tmp_cubelist = fix_cubelist_before_concat(tmp_cubelist, __current_dataset, model, freq)

        ### if the number of netcdf files (and cubes) >1 then 
        ### merge them together
        cube = iris.cube.CubeList.concatenate_cube(tmp_cubelist)
        
        #### Create a cubelist from cubes
        final_cubelist.extend([cube])

    return final_cubelist


### This is a wrapper for get_cubes. 
### i.e., takes the only cube out of a len=1 cubelist
def get_cube(filt_cat, constraints=None, verbose=True, nearest_lat_lon=False):

    ### Convert Pandas Series to DataFrame
    if 'pandas.core.series.Series' in str(type(filt_cat)):
        filt_cat = DataFrame([filt_cat.values], columns=filt_cat.keys() )
    
    if (len(filt_cat.index) == 1): 
        cube = get_cubes(filt_cat, constraints=constraints, verbose=verbose, \
                        nearest_lat_lon=nearest_lat_lon)
        cube = cube[0]

    if (len(filt_cat) > 1): 
        raise ValueError("Error: more than one cube present.  Try 'get_cubes' instead")
    if (len(filt_cat) == 0): 
        raise ValueError("Error: no cubes specified in catalogue.")

    return cube












'''
These only work with CMIP5 at the moment
'''



def get_cmip5_template_cube():
    '''
    Get a cube to use as a CMIP5 template
    '''
    cat  = catalogue(dataset='cmip5', Model='CMCC-CM',Experiment='historical',Var='tas',Frequency='mon')
    con  = iris.Constraint(cube_func=lambda cube: cube.var_name == 'tas') & iris.Constraint(year=2000) & iris.Constraint(month=1)
    cube = get_cubes(cat.iloc[[0]], constraints=con)
    return cube[0]


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