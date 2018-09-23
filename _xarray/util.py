import xarray as xr
import numpy as np


def eg_Dataset():
    """
    Load an example Xarray Dataset
    """
    from baspy import __baspy_path
    import os
    import warnings

    url = "https://www.unidata.ucar.edu/software/netcdf/examples/sresa1b_ncar_ccsm3-example.nc"
    nc_file = __baspy_path+'/sample_data/sresa1b_ncar_ccsm3-example.nc'

    ### Create sample_data folder if it doesn't already exist
    if not os.path.exists(__baspy_path+'/sample_data'): 
        os.makedirs(os.path.expanduser(__baspy_path+'/sample_data'))

    if (os.path.isfile(nc_file) == False):
        import urllib
        print('Downloading example netcdf file: '+url)
        urllib.urlretrieve (url, nc_file)

    ### Load file, suppressing any warnings
    ds = xr.open_dataset(nc_file)

    return ds


def eg_DataArray():
    return eg_Dataset().tas


def extract_region(ds, bounds):
    '''
    Extract region using pre-defined lat/lon bounds

    >>> bounds = bp.region.Country.china
    >>> ds     = bp.region.extract(ds, bounds)
    '''
    lats = ds.variables['lat'][:] 
    lons = ds.variables['lon'][:]
    lat_bnds, lon_bnds = list(bounds['lat_bnds']), list(bounds['lon_bnds'])
    lat_inds = np.where((lats > lat_bnds[0]) & (lats < lat_bnds[1]))[0]
    lon_inds = np.where((lons > lon_bnds[0]) & (lons < lon_bnds[1]))[0]
    ds = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))
    return ds


def extract_ts_nearest_neighbour(da, coord):
    da = da.interp( coords={'lat':coord['lat'], 'lon':coord['lon']}, 
                    method='nearest')
    return da

