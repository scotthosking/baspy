import numpy as np
import iris
import iris.coord_categorisation


'''
Iris specific utilities
'''

### Convert units
def convert_units_mm_day(cube):
    if (cube.units == 'kg m-2 s-1'):
        cube = cube * 86400.
        cube.units = 'mm day-1'
    else:
        raise ValueError('can not convert cube to mm day-1')
    return cube



def area_weighted_mean(cube):
    weights = iris.analysis.cartography.area_weights(cube)
    ts = cube.collapsed(['latitude','longitude'], iris.analysis.MEAN, weights=weights)

    ### Remove mask if present and unneeded
    if type(ts.data) == np.ma.core.MaskedArray:
        if all(ts.data.mask == False): ts.data = ts.data.data

    return ts



def extract_region(cube, bounds):

    '''
    Extract region using pre-defined lat/lon bounds

    >>> bounds = bp.region.Country.china
    >>> cube   = bp.region.extract(cube, bounds)
    '''

    keys = bounds.keys()

    if ('lon_bnds' in keys) | ('lat_bnds' in keys):

        if ('lon_bnds' in keys) & ('lat_bnds' in keys):
            cube = cube.intersection( longitude=bounds['lon_bnds'], latitude=bounds['lat_bnds'] )

        if ('lon_bnds' in keys) & ('lat_bnds' not in keys):
            cube = cube.intersection( longitude=bounds['lon_bnds'] )

        if ('lon_bnds' not in keys) & ('lat_bnds' in keys):
            cube = cube.intersection( latitude=bounds['lat_bnds'] )

    else:

        raise ValueError('Need to define lon_bnds and/or lat_bnds')

    return cube





def cube_trend(cube, var_name=None, time_coord=None):

    '''
    Currently this def for calculating trends should only be used for year-to-year cubes.
    e.g.,
        * A cube where each timeframe represents annual means 
        * A cube where each timeframe represents seasonal means (one season per year)

    Note: this definition will be replaced at some point with one that Tony is writing.
    '''

    from scipy import stats
    import iris.coords as coords

    lons, lats = cube.coord('longitude').points, cube.coord('latitude').points

    ### Define years for trend analysis
    years = []
    if len(cube.coords('year')) > 0:        years = cube.coord('year').points
    if len(cube.coords('season_year')) > 0: years = cube.coord('season_year').points
    if len(years) == 0:
        raise ValueError("Need to assign either 'year' or 'season_year' as Auxiliary coordinates to cube")

    ### Collapse cube to correctly assign time bounds in output metadata
    if (time_coord == None): time_coord = 'time'
    cube2 = cube.collapsed(time_coord, iris.analysis.MEAN)

    slope, p_value = iris.cube.copy.deepcopy(cube2), iris.cube.copy.deepcopy(cube2)
    slope.data[:,:], p_value.data[:,:] = np.nan, np.nan

    slope.rename(var_name+'_trend')
    p_value.rename(var_name+'_trend_sig')

    slope.units = str(slope.units)+' yr-1'
    p_value.units = '1'

    for x in range(0,len(lons)):
        for y in range(0,len(lats)):
            slope.data[y,x], intercept, r_value, p_value.data[y,x], std_err = stats.linregress( years, cube.data[:,y,x] )

    return slope, p_value


def months2seasons(cube, seasons=None):

    import iris.coord_categorisation

    ### to-do: Add check that cube is monthly!!!!!!!!! 

    ### Create seasonal means (unique and specified 3-month seasons)
    if (seasons == None):
       seasons=['mam', 'jja', 'son', 'djf']
    if len(cube.coords('clim_season')) == 0:
       iris.coord_categorisation.add_season(cube, 'time', name='clim_season', seasons=seasons)
    if len(cube.coords('season_year')) == 0:
       iris.coord_categorisation.add_season_year(cube, 'time', name='season_year', seasons=seasons)

    # Keep only those times where we can produce seasonal means using exactly 3 months
    # (i.e., remove times from cubelist where only 1 or 2 times exist for that season)
    clim_seasons = cube.coord('clim_season').points
    season_years = cube.coord('season_year').points
    ntimes       = len(cube.coord('time').points)

    keep_ind = np.zeros((0), dtype=np.int)
    for i in range(0,ntimes):
       ind = np.where( (clim_seasons == clim_seasons[i]) & (season_years == season_years[i]) )[0]
       n_months_in_season = len(clim_seasons[i]) # length of string, usually 3 (e.g. 'djfm'=4)
       if (len(ind) == n_months_in_season): keep_ind = np.append(keep_ind,i)
    time_axis = cube.coord_dims(cube.coord(axis='t'))[0]
    cube_slice = ((slice(None),) * time_axis + (keep_ind,) + (slice(None),) * (len(cube.shape) - time_axis - 1))
    cube = cube[cube_slice]

    seasons = cube.aggregated_by(['clim_season', 'season_year'], iris.analysis.MEAN)
    return seasons



def months2annual(cube):

    import iris.coord_categorisation

    ### to-do: Add check that cube is monthly!!!!!!!!! 

    if len(cube.coords('year')) == 0:
       iris.coord_categorisation.add_year(cube, 'time', name='year')

    if len(cube.coords('month')) == 1:       cube.remove_coord('month')
    if len(cube.coords('clim_season')) == 1: cube.remove_coord('clim_season')
    if len(cube.coords('season_year')) == 1: cube.remove_coord('season_year')

    ### Keep only those times where we can produce annual means using exactly 12 months
    years = cube.coord('year').points
    ntimes = len(cube.coord('time').points)

    keep_ind = np.zeros((0), dtype=np.int)
    for i in range(0,ntimes):
       ind = np.where( (years == years[i]) )[0]
       n_months_in_year = 12
       if (len(ind) == n_months_in_year): keep_ind = np.append(keep_ind,i)
    time_axis = cube.coord_dims(cube.coord(axis='t'))[0]
    cube_slice = ((slice(None),) * time_axis + (keep_ind,) + (slice(None),) * (len(cube.shape) - time_axis - 1))
    cube = cube[cube_slice]

    annual = cube.aggregated_by(['year'], iris.analysis.MEAN)
    return annual


def unify_similar_grid_coords(cubes, cube_template=None):
    """
    If the x or y coordinates are similar but different from a template cube then make them the same.
    If cube_template is not specified then default to the first cube in the cubelist.
    
    Examples:
        cubelist = bp.util.unify_similar_grid_coords(cubelist)
        cubes = bp.util.unify_similar_grid_coords(cubes, cube_template=cubes[0])
    """

    if (type(cubes) == iris.cube.Cube):
        cubes = iris.cube.CubeList([cubes])

    if (cube_template == None):
        cube_template = cubes[0]

    if (type(cube_template) != iris.cube.Cube):
        raise ValueError('cube_template is not a cube')


    if (len(cube_template.coords(axis='X')) == 1) & (len(cube_template.coords(axis='Y')) == 1):

        for axis in ['X', 'Y']:
            if 'NoneType' in str(type(cube_template.coord(axis=axis).bounds)):
                cube_template.coord(axis=axis).guess_bounds()
        
        if len(cubes) > 0:
            for i, cube in enumerate(cubes):
                for axis in ['X', 'Y']:
                     
                    if (np.any(cube.coord(axis=axis).points != cube_template.coord(axis=axis).points) and
                            np.all(np.isclose(cube.coord(axis=axis).points, cube_template.coord(axis=axis).points))):
                            cube.coord(axis=axis).points = cube_template.coord(axis=axis).points
                            cubes[i] = cube

                    if 'NoneType' in str(type(cube.coord(axis=axis).bounds)):
                            cube.coord(axis=axis).bounds = cube_template.coord(axis=axis).bounds
                            cubes[i] = cube

                    if (np.any(cube.coord(axis=axis).bounds != cube_template.coord(axis=axis).bounds) and
                            np.all(np.isclose(cube.coord(axis=axis).bounds, cube_template.coord(axis=axis).bounds))):
                            cube.coord(axis=axis).bounds = cube_template.coord(axis=axis).bounds
                            cubes[i] = cube

                    if (axis == 'X'):
                            cube.coord(axis=axis).circular = cube_template.coord(axis=axis).circular
                            cubes[i] = cube

    else:
        print("WARNING: Can not attempt to unify similar cube coordinates as more than one coord associated with axis='X' and/or axis='Y' ")

    return cubes




def rm_time_overlaps(cubelist):
    """
    Remove time overlaps from a cubelist
    keeping the duplicated period from the cube that
    comes first within the cubelist
    """    
    if (cubelist.__class__ != iris.cube.CubeList):
        raise ValueError('rm_time_overlaps requires a cubelist')
    
    if (len(cubelist) == 1): return cubelist
    
    ### Check that all cubes have the same var_name
    var_names = [c.var_name for c in cubelist]
    all_same = all(x==var_names[0] for x in var_names)
    if all_same == False:
        raise ValueError('cubelist contains cubes with difference var_names')
    
    ### Unify time coordinates to identify overlaps
    iris.util.unify_time_units(cubelist)
    
    ### Sort cubelist by start time
    cubelist.sort(key=lambda cube: cube.coord(axis='t').points[0])
    ### Tony: potentially a more robust robust solution??
    ### cubelist.sort(key=lambda cube: cube.coord(axis='t').units.num2date(cube.coord(axis='t').points[0]))


    i = 1
    while i < len(cubelist):

        max1 = np.max(cubelist[i-1].coord(axis='t').points)
        min2 = np.min(cubelist[i].coord(axis='t').points)
        
        if (min2 <= max1):
            print('>>> WARNING: Removing temporal overlaps'
                    ' from cubelist <<<')
            print(min2, max1)
            with iris.FUTURE.context(cell_datetime_objects=False):
                con = iris.Constraint(time=lambda t: t > max1)
                cubelist[i] = cubelist[i].extract(con)

        if (cubelist[i].__class__ != iris.cube.Cube):
            cubelist.pop(i)
        else:
            i = i + 1
    
    return cubelist


def eg_cubelist():
    """
    Load an example cubelist
    """
    from baspy import __baspy_path
    import os
    import warnings

    url = "https://www.unidata.ucar.edu/software/netcdf/examples/sresa1b_ncar_ccsm3-example.nc"
    file = __baspy_path+'/sample_data/sresa1b_ncar_ccsm3-example.nc'

    ### Create sample_data folder if it doesn't already exist
    if not os.path.exists(__baspy_path+'/sample_data'): 
        os.makedirs(os.path.expanduser(__baspy_path+'/sample_data'))

    if (os.path.isfile(file) == False):
        import requests
        print('Downloading sample file: '+url.split('/')[-1])
        r = requests.get(url)
        with open(file, 'wb') as f:  
            f.write(r.content)

    ### Load file, suppressing any warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        cubelist = iris.load(file, ['air_temperature', 'eastward_wind', 'precipitation_flux'])

    return cubelist


def eg_cube():
    """ 
    Load an example cube
        cube = bp.eg_cube()
    """
    cube = eg_cubelist()
    return cube[0]


def remove_aux_coord(cube, coord_name):
    '''
    Remove auxillary coord from cube if already exists (otherwise ignore/do nothing)
    '''
    aux_coords = [aux_coord.long_name for aux_coord in cube.aux_coords]
    if coord_name in aux_coords: 
        cube.remove_coord(coord_name)
    return cube


def create_ensemble_cube(cubelist, coord_labels, long_name=None, units=None):
    '''
    e.g., For creating one cube from many ensemble members.

    cube_merged = create_ensemble_cube(cubelist, [1,2,3,4], 'RunID')

    use if cubelist.merge_cube() does not work
    '''
    for i, cube in enumerate(cubelist):
        cube = remove_aux_coord(cube, long_name)
        new_coord = iris.coords.AuxCoord(coord_labels[i], long_name=long_name, units=units)
        cube.add_aux_coord(new_coord)
        cubelist[i] = cube

    new_cube = cubelist.merge_cube()

    return new_cube



def make_ts_cube(ts, cube, rename=None, units=None):
    '''
    Make a 1D time-series cube based on another cube with the same time coordinate system

    add_scalar_coords: 
        see bp.util.add_scalar_coords def for more info

    '''

    ### Setup new name, units etc (default is to keep the same)
    if (rename != None): cube.rename(rename)
    if (units == None): units=cube.units
    long_name=cube.long_name

    ts = np.squeeze(ts)
    new_cube = iris.cube.Cube( np.zeros(ts.shape), long_name=long_name, units=units )

    ### Copy time coordinates and all attributes from original cube    to new cube
    t_coord = cube.coord(axis='t')
    new_cube.add_dim_coord(t_coord, 0)

    for coord in cube.aux_coords: 
        if len(coord.points) == 1: data_dims=None
        if len(coord.points) == len(t_coord.points): data_dims=0 ### Generalise this!!!!!!!!!!!!!!!!
        new_cube.add_aux_coord(coord, data_dims=data_dims)

    new_cube.attributes = cube.attributes

    ### Remove mask if present and unneeded
    if type(ts) == np.ma.core.MaskedArray:
        if all(ts.mask == False): ts = ts.data

    ### Copy time series into new cube
    new_cube.data = ts
    
    return new_cube
    

def add_scalar_coords(cube, coord_dict=None):
    '''
    Useful for adding, e.g., longitude and latitude to a 1D time series cube at a specific location

    coord_dict needs to be a dictionary of the form:
        {'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}"

    '''

    if (type(coord_dict) != dict):
        raise ValueError("coord_dict needs to be a dictionary of the form: \
                            {'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}")

    import iris.coords as coords

    for key, values in coord_dict.iteritems():

        if (type(values) != list) | (len(values) != 2):
            ValueError("coord_dict must of the form: {'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}")
        
        scalar = values[0]
        units  = values[1]
        new_coord = coords.AuxCoord(scalar, long_name=key, units=units)
        cube.add_aux_coord(new_coord)

    return cube



def region_mask(cube, region_name):

    # mask cube to country
    import cartopy.io.shapereader as shpreader
    import itertools
    from iris.analysis.geometry import geometry_area_weights
    import numpy.ma as ma

    ### Guess bounds if currently not specified
    if cube.coord('latitude').bounds == None:  cube.coord('latitude').guess_bounds()
    if cube.coord('longitude').bounds == None: cube.coord('longitude').guess_bounds()
     
    # get countries (resolution = 10m, 50m, 110m )
    shpfilename = shpreader.natural_earth(category='cultural',name='admin_0_countries',resolution='110m')
    reader = shpreader.Reader(shpfilename)

    # list available attributes
    all_countries = reader.records()
    country = next(all_countries)
    # print(country.attributes.keys())

    # get all values of an attribute
    key = 'name_long'
    values = set()
    all_countries = reader.records()
    for country in all_countries: values.add( country.attributes[key] )
    # print( key+': '+ ', '.join(values) )

    # extract countries matching criteria - is there an easier way???
    country_crit = lambda country: country.attributes['name_long'] == region_name  ## e.g., 'China'
    # country_crit = lambda country: country.attributes['continent'] == 'Asia'
    # country_crit = lambda country: country.attributes['region_un'] == 'Asia'
    # country_crit = lambda country: country.attributes['subregion'] == 'Eastern Asia'

    all_countries = reader.records()
    countries = itertools.ifilter(country_crit, all_countries)

    # work out area weights of single field's intersection with selected countries
    # !!! need to make generic (get first field from cube)

    country = next(countries)
    print( 'Getting field intersection area with '+country.attributes['name_long'] )
    area_weights = geometry_area_weights(cube, country.geometry)

    for country in countries:
        print( 'Getting field intersection area with '+country.attributes['name_long'] )
        area_weights += geometry_area_weights(cube, country.geometry)

    # create a mask from the area weights
    mask = np.where(area_weights > 0, False, True)

    masked_cube = cube.copy()

    # NB: this combines the mask and the data's existing mask as required
    masked_cube.data = ma.array(masked_cube.data, mask=mask)

    return masked_cube




# End of util.py
