import numpy as np
import datetime
import os.path, glob
import xarray as xr
from baspy import __baspy_path
import pandas as pd

root = '/group_workspaces/jasmin4/bas_climate/data/ecmwf'

### Create folder for storing data
if not os.path.exists(__baspy_path):
    os.makedirs(os.path.expanduser(__baspy_path))


def create_6hr_catalogue():

    from dateutil import parser
    import pandas as pd
    datelist = pd.date_range(start='1979-01-01', end='2025-01-01', freq='D')    
    filenames, date_store, level_store = [], [], []

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
    df.to_csv(__baspy_path+'/era-interim_6hr_catalogue.csv', index=False)

    return df


# df = create_6hr_catalogue()


def get_erai_6h_cat(start_date, end_date, level=None, verbose=True):
   
    from dateutil import parser

    if level == None:
        print("'level' undefined, setting to 'as' (surface). Alt option 'ap' (pressure level data) ")
        level = 'as'

    ### read in catalogue
    df = pd.read_csv(__baspy_path+'/era-interim_6hr_catalogue.csv') 

    ### Filter by level type (surface or pressure, as or ap)
    df = df[ df['Level'] == level ]

    ### Filter by dates
    start_datetime = parser.parse(start_date)
    end_datetime   = parser.parse(end_date)
    dates = pd.DatetimeIndex(df['Date'])
    df = df[ (dates >= start_datetime) & (dates < end_datetime) ]

    return df


out_dir_root = '/group_workspaces/jasmin4/bas_climate/data/ecmwf/era-interim/day'

for yr in range( 1979, 2019 ):
    df = get_erai_6h_cat(str(yr)+'-01-01', str(yr+1)+'-01-01', level='ap')
    ds = xr.open_mfdataset(df['Filename'].values)
    da = ds.U.sel(p=850).groupby('t.dayofyear').mean(dim='t')

    out_dir = out_dir_root + '/U850hPa'
    if not os.path.exists(out_dir):
        print('mkdir '+out_dir)
        os.makedirs(os.path.expanduser(out_dir))
    
    da.to_netcdf(path=out_dir+'/U850hPa_'+str(yr)+'.nc', mode='w')