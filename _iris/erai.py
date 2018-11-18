import os
import numpy as np
import datetime
import os.path
import cf_units as units
import iris
from baspy import __baspy_path
import pandas as pd

erai_catalogue_file = __baspy_path+'/era-interim_6hr_catalogue.csv'

root = '/group_workspaces/jasmin4/bas_climate/data/ecmwf'

### Create folder for storing data
if not os.path.exists(__baspy_path):
    os.makedirs(os.path.expanduser(__baspy_path))



def create_6hr_catalogue():

    from dateutil import parser
    import pandas as pd
    datelist = pd.date_range(start='1979-01-01', end='2025-01-01', freq='D')    
    filenames, date_store, level_store = [], [], []

    print('Creating ERA-Interim catalogue.')

    for level in ['as', 'ap']:
        
        for date in datelist:
            yr       = str(date.year)
            mon      = str("{:0>2d}".format(date.month))
            day      = str("{:0>2d}".format(date.day))
            
            directory = root+'/era-interim/6hr/gg/'+level+'/'+yr+ \
                            '/'+mon+'/'+day+'/'

            if os.path.exists(directory):
                files = glob.glob(directory+'/*.nc')
                if len(files) == 4:
                    for file in files:
                        filenames.append(file)
                        date_str = parser.parse(file.split('/')[-1][4:-3])
                        date_store.append(date_str)
                        level_store.append(level)

    ### write to dataframe
    df = pd.DataFrame()
    df['Date']          = date_store
    df['Level']         = level_store
    df['Frequency']     = '6h'
    df['Filename']      = filenames

    print('Saving ERA-Interim catalogue to csv')
    df.to_csv(erai_catalogue_file, index=False)

    return df


def get_erai_6h_cat(start_date, end_date, level=None, verbose=True):
   
    from dateutil import parser

    if level == None:
        print("'level' undefined, setting to 'as' (surface level data). \n" + \
                " Alt option 'ap' (pressure level data) ")
        level = 'as'

    ### read in catalogue
    if not os.path.exists(erai_catalogue_file):
        df = create_6hr_catalogue()
    else:
        df = pd.read_csv(erai_catalogue_file) 

    ### Filter by level type (surface or pressure, as or ap)
    df = df[ df['Level'] == level ]

    ### Filter by dates
    start_datetime = parser.parse(start_date)
    end_datetime   = parser.parse(end_date)
    dates = pd.DatetimeIndex(df['Date'])
    df = df[ (dates >= start_datetime) & (dates < end_datetime) ]

    return df


def level_from_var_name(var_name):
    ### Get level_str from var_name
    level_str = None
    df_as = pd.read_csv(root+'/era-interim/era-interim_6hrly_surface_vars.csv')
    df_ap = pd.read_csv(root+'/era-interim/era-interim_6hrly_pressure_lev_vars.csv')
    if var_name in df_as['surface_vars'].values:      level_str = 'as'
    if var_name in df_ap['pressure_lev_vars'].values: level_str = 'ap'
    if level_str == None: 
        print('Surface Vars        =', df_as['surface_vars'].values)
        print('Pressure Level Vars =', df_ap['pressure_lev_vars'].values)
        raise ValueError('Can not find files for var_name='+var_name)
    return level_str


def edit_erai_attrs(cube, field, filename):
    ### Remove attributes from cube on read
    cube.attributes.pop('history', None)
    cube.attributes.pop('time',    None)
    cube.attributes.pop('date',    None)
    cube.attributes.pop('valid_max',    None)
    cube.attributes.pop('valid_min',    None)
    cube.coord('t').attributes.pop('time_origin', None)


def get_cube(start_date, end_date, var_name, frequency='6hr', 
                constraints=None, verbose=True):

    """

    Get /Path/filenames for ERA-Interim files within date range

    Start and end date can be specified using a range of strings:
            e.g., '19790101', '1979-01-01', '19790101010101'

    var_name is a constraint on the cube variable name (i.e., cube.var_name)
        e.g., var_name = 'T2'

    """

    ### Iris v2.2 hangs when saving netcdf files, use NETCDF3-CLASSIC 
    ### as a workaround - SH

    level = level_from_var_name(var_name)

    if frequency == '6hr': 
        df = get_erai_6h_cat(start_date, end_date, level, verbose=verbose)
    else:
        raise ValueError('Only 6hr frequency currently supported')
    
    con = iris.Constraint(cube_func=lambda cube: cube.var_name == var_name)
    
    ### Additional constrains (level, time)
    if (constraints != None): con = con & constraints

    fnames = df['Filename'].values
    print('first & last files=', fnames[0].split('/')[-1], fnames[-1].split('/')[-1])
    with units.suppress_errors():
        cubelist = iris.load(fnames, constraints=con, 
                                callback=edit_erai_attrs)

    ### Setup new coord to add to cube (see below)
    model_coord = iris.coords.AuxCoord('ERA-Interim', long_name='Model', 
                                            units='no_unit')

    ### Fix cubes to all match a reference cube before we can merge
    ref = cubelist[0]
    for c in cubelist: 
        c.coord('latitude').points         = ref.coord('latitude').points
        c.coord('longitude').points        = ref.coord('longitude').points
        c.coord('latitude').standard_name  = ref.coord('latitude').standard_name
        c.coord('longitude').standard_name = ref.coord('longitude').standard_name
        c.add_aux_coord(model_coord)       # Add model name as a scalar coord

    iris.util.unify_time_units(cubelist)
    cube = cubelist.concatenate_cube()
    cube = iris.util.squeeze(cube)

    return cube


def get_land_mask():
    with units.suppress_errors():
        cube = iris.load_cube(root+'/era-interim/erai_invariant.nc', 
                                'land_binary_mask')
    return cube
