import xarray as xr
import numpy as np


def eg_Dataset():
    """
    Load an example Xarray Dataset
    """
    from esmcat import __esmcat_path
    import os
    import warnings

    url = 'http://esgdata.gfdl.noaa.gov/thredds/fileServer/' + \
            'gfdl_dataroot3/CMIP/NOAA-GFDL/GFDL-AM4/amip/' + \
            'r1i1p1f1/Amon/tas/gr1/v20180807/' + \
            'tas_Amon_GFDL-AM4_amip_r1i1p1f1_gr1_198001-201412.nc'

    file = __esmcat_path+'/sample_data/'+url.split('/')[-1]

    if not os.path.exists(__esmcat_path+'/sample_data'):
        os.makedirs(os.path.expanduser(__esmcat_path+'/sample_data'))

    if (os.path.isfile(file) == False):
        import requests
        print('Downloading sample CMIP6 file: '+url.split('/')[-1])
        r = requests.get(url)
        with open(file, 'wb') as f:
            f.write(r.content)

    ds = xr.open_dataset(file)

    return ds


def eg_DataArray():
    return eg_Dataset().tas


def extract_region(da, bounds):
    lat_bnds, lon_bnds = list(bounds['lat_bnds']), list(bounds['lon_bnds'])
    da = da.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    return da


def extract_ts_nearest_neighbour(da, coord):
    da = da.interp( coords={'lat':coord['lat'], 'lon':coord['lon']},
                    method='nearest')
    return da
