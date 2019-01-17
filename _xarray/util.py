import xarray as xr
import numpy as np


def eg_Dataset():
    """
    Load an example Xarray Dataset
    """
    from baspy import __baspy_path
    import os
    import warnings

    url = 'http://esgdata.gfdl.noaa.gov/thredds/fileServer/' + \
            'gfdl_dataroot3/CMIP/NOAA-GFDL/GFDL-AM4/amip/' + \
            'r1i1p1f1/Amon/tas/gr1/v20180807/' + \
            'tas_Amon_GFDL-AM4_amip_r1i1p1f1_gr1_198001-201412.nc'

    file = __baspy_path+'/sample_data/'+url.split('/')[-1]

    ### Create sample_data folder if it doesn't already exist
    if not os.path.exists(__baspy_path+'/sample_data'): 
        os.makedirs(os.path.expanduser(__baspy_path+'/sample_data'))

    if (os.path.isfile(file) == False):
        import requests
        print('Downloading sample CMIP6 file: '+url.split('/')[-1])
        r = requests.get(url)
        with open(file, 'wb') as f:  
            f.write(r.content)

    ### open file
    ds = xr.open_dataset(file)

    return ds


def eg_DataArray():
    return eg_Dataset().tas


def extract_region(da, bounds):
    '''
    Extract region using pre-defined lat/lon bounds

    >>> bounds = bp.region.Country.china
    >>> da     = bp.region.extract(da, bounds)
    '''
    lat_bnds, lon_bnds = list(bounds['lat_bnds']), list(bounds['lon_bnds'])
    da = da.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    # lats = da['lat'][:] 
    # lons = da['lon'][:]
    # lat_inds = np.where((lats > lat_bnds[0]) & (lats < lat_bnds[1]))[0]
    # lon_inds = np.where((lons > lon_bnds[0]) & (lons < lon_bnds[1]))[0]
    return da


def extract_ts_nearest_neighbour(da, coord):
    da = da.interp( coords={'lat':coord['lat'], 'lon':coord['lon']}, 
                    method='nearest')
    return da

