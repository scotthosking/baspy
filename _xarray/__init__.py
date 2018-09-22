from . import util
import xarray as xr


eg_Dataset   = util.eg_Dataset
eg_DataArray = util.eg_DataArray


def open_dataset(df, **kwargs):

    ### sanity checks
    if 'pandas.core.frame.DataFrame' not in str(type(df)):
        raise ValueError('not a Pandas DataFrame')
    if len(df) != 1:
        raise ValueError('Catalogue contains more than one row')

    directory = df['Path'].values[0]+'/'
    files     = df['DataFiles'].values[0].split('|')
    files     = [ directory+f for f in files ]
    ds        = xr.open_mfdataset(files) 

    return ds