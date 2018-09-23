from . import util
import xarray as xr

eg_Dataset   = util.eg_Dataset
eg_DataArray = util.eg_DataArray

def open_dataset(df, **kwargs):
    ds = xr.open_mfdataset(bp.get_files(df)) 
    return ds