import baspy as bp
import xarray as xr

''' 
Define scope of CMIP6 that we want (our catalogue)
* amip = atmosphere-only run (with transient/observed sea surface temperatures)
* tasmin,tasmax = minimum/maximum temperature over period
* CMOR (Climate Model Output Rewriter), defines, amongst other things, the temporal 
    frequency of the data (monthly, daily etc)
    see: https://github.com/PCMDI/cmip6-cmor-tables/tree/master/Tables
* Model = our chosen CMIP6 climate model
* RunID = the run ID :-)
'''
catlg = bp.catalogue(dataset='cmip6', Experiment='amip', 
                        Var=['tasmax','tasmin'], CMOR='day', 
                        Model='CNRM-CM6-1', RunID='r1i1p1f2')

''' Read Datasets using BASpy wrapper for Xarray '''
tasmin_ds = bp.open_dataset(catlg[catlg.Var == 'tasmin'])
tasmax_ds = bp.open_dataset(catlg[catlg.Var == 'tasmax'])

''' extract DataArray from Dataset '''
tasmin = tasmin_ds.tasmin
tasmax = tasmax_ds.tasmax


''' 
Now analyse CMIP6 data using the Xarray framework 
[1] http://xarray.pydata.org/en/stable/
[2] https://github.com/scotthosking/notebooks/blob/master/getting_started_with_Xarray%2BDask.ipynb
'''
