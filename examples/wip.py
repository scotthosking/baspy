from pandas import DataFrame
import baspy as bp
import xarray as xr
import numpy as np


######################
### read example data
######################
catlg = bp.catalogue(Var=['tas'], Frequency='mon', 
                        Experiment='historical', Model='HadGEM2-ES',
                        RunID='r1i1p1')
catlg = catlg.iloc[0]
ds    = xr.open_mfdataset(bp.get_files(catlg), concat_dim='time') 

da = ds.tas

### Add an attribute
da.attrs.update(Analyst='Dr Scott Hosking, jask@bas.ac.uk')


######################################
### Resample / Interpolation
######################################
lons_new = np.linspace(0., 5.5, 10)
lats_new = np.linspace(0., 5.5, 10)
da1 = da.interp(coords={'lat':lats_new, 'lon':lons_new}, 
                    method='linear')
