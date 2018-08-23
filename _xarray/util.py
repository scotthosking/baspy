import xarray as xr


def eg_DataArray():
    """
    Load an example cubelist
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
