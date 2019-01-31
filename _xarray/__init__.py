from . import util
import xarray as xr
from baspy import get_files

def open_dataset(df): 
    files = get_files(df)
    if len(files) == 1:
        ds = xr.open_dataset(files[0])
    else:
        ds = xr.open_mfdataset(files)
    return ds
