import numpy as np
import datetime
import os.path, glob
import xarray as xr
from baspy import __baspy_path
import baspy as bp
import pandas as pd

get_erai_6h_cat = bp._iris.era.get_erai_6h_cat

out_dir_root = '/group_workspaces/jasmin4/bas_climate/data/ecmwf/era-interim/day_xr_test'

for yr in range( 1979, 2018 ):
    df = get_erai_6h_cat(str(yr)+'-01-01', str(yr+1)+'-01-01', level='ap')
    ds = xr.open_mfdataset(df['Filename'].values)
    da = ds.U.sel(p=850)

    out_dir = out_dir_root + '/U850hPa'
    if not os.path.exists(out_dir):
        print('mkdir '+out_dir)
        os.makedirs(os.path.expanduser(out_dir))
    
    da = da.groupby('t.dayofyear').mean(dim='t')
    print('writing: U850hPa_'+str(yr)+'.nc')
    da.to_netcdf(path=out_dir+'/U850hPa_'+str(yr)+'.nc', mode='w')