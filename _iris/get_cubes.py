import re
from pandas.core.series import Series
from pandas import DataFrame


### This should be merged with get_cubes2 once that has been generisied
def get_cubes(filt_cat, constraints=None, verbose=True, nearest_lat_lon=False):

	### Convert Pandas Series to DataFrame
	if type(filt_cat) == Series:
		filt_cat = DataFrame([filt_cat.values], columns=filt_cat.keys() )

	### Which dataset are we working with?
	df0       = filt_cat.iloc[0]
	path0     = df0['Path']
	split_str = re.split('/', path0)

	if ('cmip5' in split_str):
		import baspy.cmip5
		cubes = baspy.cmip5.get_cubes(filt_cat, constraints=constraints, verbose=verbose,
										nearest_lat_lon=nearest_lat_lon)

	if ('happi' in split_str):
		import baspy.happi
		cubes = baspy.happi.get_cubes(filt_cat, constraints=constraints, verbose=verbose,
										nearest_lat_lon=nearest_lat_lon)

	return cubes








#### NEW VERSION TO REPLACE GET_CUBES ABOVE


'''
A general module for cataloguing and reading in data
that conforms to the CMIP directory structure and filename format

including:
* CMIP5
* HAPPI
* CMIP6 ?
* ERAI ?

'''


def callback(cube, field, filename):
    """
    A function which adds a "RunID" coordinate to the cube

    To do:
    	use the FileStructure from the dataset_dictionary
    	and add all the important elements as AuxCoords
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


def get_cubes2(filt_cat, constraints=None, verbose=True):
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
        

        ### ADD FIXES HERE ###
        ### include in another file !!!!


        ### if the number of netcdf files (and cubes) >1 then 
        ### merge them together
        cube = iris.cube.CubeList.concatenate_cube(cubelist1)
        
        #### Create a cubelist from cubes
        cubelist2.extend([cube])

    return cubelist2









### This is a wrapper for get_cubes - takes the cube out of a len=1 cubelist
def get_cube(filt_cat, constraints=None, verbose=True, nearest_lat_lon=False):

	### Convert Pandas Series to DataFrame
	if type(filt_cat) == Series:
		filt_cat = DataFrame([filt_cat.values], columns=filt_cat.keys() )

	if (len(filt_cat.index) == 1): 
		cube = get_cubes(filt_cat, constraints=constraints, verbose=verbose, 
							nearest_lat_lon=nearest_lat_lon)
		cube = cube[0]

	if (len(filt_cat) > 1): 
		raise ValueError("Error: more than one cube present.  Try 'get_cubes' instead")
	if (len(filt_cat) == 0): 
		raise ValueError("Error: no cubes specified in catalogue.")

	return cube
