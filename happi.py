import glob
import re
import os
import pandas as pd
import iris
import iris.coords as coords
import baspy.util
import numpy as np

### Setup catalogue file (copy over if needs be)
copied_new_cat_file, cat_file, __shared_cat_file = baspy._catalogue.setup_catalogue_file('happi')


def __refresh_shared_catalogue():
    '''
    Rebuild the HAPPI catalogue
    '''

    print("Building catalogue now...")

    ### Get paths for all HAPPI data
    happi_dir = '/group_workspaces/jasmin4/bas_climate/data/happi/'
    paths1 = glob.glob(happi_dir+'data/*/*/*/*/*/*/*/*/*')
    paths2 = glob.glob(happi_dir+'derived/*/*/*/*/*/*/*/*/*')
    paths  = paths1 + paths2
    paths  = filter(lambda f: os.path.isdir(f), paths)

    ### write data to catalogue (.csv) using a Pandas DataFrame
    rows = []
    for path in paths:

        parts = re.split('/', path)[7:]

        ### Make list of file names: i.e., 'file1.nc|file2.nc'
        included_extensions = ['.nc', '.nc4', '.pp', '.grib']
        fnames = [fn for fn in os.listdir(path) if any(fn.endswith(ext) for ext in included_extensions)]
        files_str = ';'.join(fnames)

        ### Only add a row for paths where we have data files
        if len(fnames) > 0:
            start_date, end_date = get_cmip_file_date_ranges(fnames)

            ### Append parts in correct order
            parts.append(int(np.min(start_date)))
            parts.append(int(np.max(end_date)))
            parts.append(path)    
            parts.append(files_str)

            ### Append new row
            rows.append(parts)

    df = pd.DataFrame(rows, columns=['Centre','Model','Experiment','CMOR','Version','Frequency','SubModel','Var','RunID',
                                        'StartDate', 'EndDate', 'Path','DataFiles', ])

    ### save to local dir
    df.to_csv(cat_file, index=False)

    if os.path.exists(__shared_cat_file):
        ### We have access to __shared_cat_file
        print('Copying new catalogue to '+__shared_cat_file)
        import shutil
        shutil.copy2(cat_file, __shared_cat_file)



def get_cmip_file_date_ranges(fnames):
    ### Get start and end dates from file names
    start_date = np.array([])
    end_date   = np.array([])
    for fname in list(fnames):
        fname = os.path.splitext(fname)[0] # rm extention
        date_range = re.split('_', fname)[-1]
        start_date = np.append( start_date, int(re.split('-', date_range)[0]) )
        end_date   = np.append( end_date,   int(re.split('-', date_range)[1]) )
    return start_date, end_date



def callback(cube, field, filename):
    """
    A function which adds a "RunID" coordinate to the cube
    """

    filename  = re.split('/',filename)[-1]
    split_str = re.split('_',filename)

    ### Extract the Model name from the filename
    new_coord = coords.AuxCoord(split_str[2], long_name='Model', units='no_unit')
    cube.add_aux_coord(new_coord)

    ### Extract the Experiment name from the filename
    new_coord = coords.AuxCoord(split_str[3], long_name='Experiment', units='no_unit')
    cube.add_aux_coord(new_coord)

    ### Extract the RunID name from the filename
    new_coord = coords.AuxCoord(split_str[6], long_name='RunID', units='no_unit')
    cube.add_aux_coord(new_coord)

    ### Add additional time coordinate categorisations
    if (len(cube.coords(axis='t')) > 0):
        time_name = cube.coord(axis='t').var_name
        iris.coord_categorisation.add_year(cube, time_name, name='year')
        iris.coord_categorisation.add_month_number(cube, time_name, name='month')
        seasons = ['djf', 'mam', 'jja', 'son']
        iris.coord_categorisation.add_season(cube, time_name, name='clim_season', seasons=seasons)
        iris.coord_categorisation.add_season_year(cube, time_name, name='season_year', seasons=seasons)




def get_cubes(filt_cat, constraints=None, verbose=True):
    """
    Use filtered catalogue to read files and return a CubeList

    >>> cat      = bp.happi.catalogue(Experiment='historical', Frequency='mon', Var='psl')
    >>> cubelist = bp.happi.get_cubes(cat)
    """

    ### start with empty cubelist, then expand within loop
    cubelist2 = iris.cube.CubeList([])

    count = 0
    len_filt = len(filt_cat.index)

    for i in filt_cat.index:
        filt    = filt_cat[filt_cat.index == i]
        path    = filt['Path'].values[0]
        centre  = filt['Centre'].values[0]
        model   = filt['Model'].values[0]
        run_id  = filt['RunID'].values[0]
        var     = filt['Var'].values[0]
        exp     = filt['Experiment'].values[0]
        freq    = filt['Frequency'].values[0]
        netcdfs = re.split(';', filt['DataFiles'].values[0] )
        
        print(netcdfs) # TMP!!!

        ### Print progress to screen
        if (verbose == True): 
            count = count+1
            print('['+str(count)+'/'+str(len_filt)+'] HAPPI '+centre+' '+model+' '+run_id+' '+exp+' '+var)

        ### Sanity check: Check that filenames represent what we requested
        for nc in netcdfs:
            if (model not in nc) | (var not in nc) | (run_id not in nc) | (exp not in nc):
                raise ValueError('>> WARNING: Detected misplaced files in '+path+' <<')

        ### List file names that appear to be within our date range
        # if (start_date != None) | (end_date != None):
        #     file_date_range = get_cmip_file_date_ranges(netcdfs)
        #     if (start_date == None): start_date = np.min(file_date_range[0])
        #     if (end_date == None):   end_date   = np.max(file_date_range[1])

        #     keep_ind1 = np.where( (end_date >= file_date_range[0])   & (end_date <= file_date_range[1])   )[0]
        #     keep_ind2 = np.where( (start_date >= file_date_range[0]) & (start_date <= file_date_range[1]) )[0]
        #     keep_ind  = np.sort(np.unique(np.append(keep_ind1,keep_ind2)))
            
        #     if (len(keep_ind) == 0): 
        #         raise ValueError("No netcdf files within requested date range")
        #     else:
        #         netcdfs = netcdfs[keep_ind]

        # if type(netcdfs) == str: netcdfs=[netcdfs]
        
        # print netcdfs # TMP!!!


        ### Read data with callback to add Experiment (Run) ID to 
        ### distinguish between ensemble memebers
        cubelist1 = iris.cube.CubeList([])
        for j in netcdfs:
            dirfilename = path+'/'+j
            ### contraint by var_name
            con = iris.Constraint(cube_func=lambda cube: cube.var_name == var)
            
            ### Additional constrains (level, time)
            if (constraints != None): con = con & constraints
            
            cube = iris.load(dirfilename, callback=callback, constraints=con)

            if (len(cube) > 1): raise ValueError('more than one cube loaded, expected only one!')

            if ( (type(cube) == iris.cube.CubeList) & (len(cube) == 1) ):    
                cube = cube[0]
            
                ### Remove attributes to enable cubes to concatenate
                cube.attributes.clear() ### To do - keep/unify attributes!!!
                
                ### Create cubelist from cubes
                cubelist1.extend([cube])

        ### Change reference time of cubes so times match in order to 
        ### encourage cubes to concatenate
        iris.util.unify_time_units(cubelist1)
        
        ### Remove temporal overlaps
        cubelist1 = baspy.util.rm_time_overlaps(cubelist1)

        ### Unify lat-lon grid
        #cubelist1 = baspy.util.unify_grid_coords(cubelist1, cubelist1[0])
        

        ### fix for HAPPI MIROC monthly data to allow cubes to concatenate (e.g., All-Hist, ua, run001)
        ### --- Make this more generic for all models !!!!
        if (model == 'MIROC5') & (freq == 'mon'):
            for c in cubelist1:
                coords = [dc.long_name for dc in c.dim_coords]
                for axis in coords:
                    if c.coord(axis).points.dtype == 'float64':
                        c.coord(axis).points  = c.coord(axis).points.astype('float32')
                for axis in ['time','latitude','longitude']:
                       if c.coord(axis).bounds.dtype == 'float64':
                        c.coord(axis).bounds  = c.coord(axis).bounds.astype('float32')
                if c.coord('time').units != cubelist1[0].coord('time').units:
                    ### note that we have already unified time coords above.
                    c.coord('time').units = cubelist1[0].coord('time').units


        ### if the number of netcdf files (and cubes) >1 then 
        ### merge them together
        cube = iris.cube.CubeList.concatenate_cube(cubelist1)
        
        #### Create a cubelist from cubes
        cubelist2.extend([cube])

    return cubelist2
