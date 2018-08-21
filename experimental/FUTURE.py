from pandas import DataFrame
import baspy as bp
import xarray as xr

'''
Wishlist for baspy v2 (should we start a new github repo?):
    * based on Xarray rather than iris
    * add start and end dates to the data catalogues
    * automatically select nc files to read based on date range
    * check lat/lon dims all match between nc files then use concat_dim=time in open_mfdataset 
        if all's well. Can record the status in CSV catalogue
    * 

'''


#########################
#########################
### Learning Xarray
#########################
#########################

### read example data
models = 'HadGEM2-ES'
experiments = ['historical', 'rcp26', 'rcp45', 'rcp85']
catlg = bp.catalogue(Var=['tas'], Frequency='day', Experiment=experiments, Model=models, RunID='r1i1p1')

ds = xr.open_mfdataset(catlg['Path'].values[0]+'/*.nc', concat_dim='time') 

### Add an attribute
ds.attrs.update(Analyst='Dr Scott Hosking, jask@bas.ac.uk')


#########################
### Extract region
#########################
lats = ds.variables['lat'][:] 
lons = ds.variables['lon'][:]
lat_bnds, lon_bnds = [40, 43], [0, 5]
lat_inds = np.where((lats > lat_bnds[0]) & (lats < lat_bnds[1]))[0]
lon_inds = np.where((lons > lon_bnds[0]) & (lons < lon_bnds[1]))[0]
extracted_ds = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))

tas = extracted_ds['tas']


#########################
### Extract nearest point
#########################

def nearest(items,pivot):
    nearest=min(items, key=lambda x: abs(x - pivot))
    timedelta = abs(nearest - pivot)
    return nearest

lats = ds.variables['lat'][:] 
lons = ds.variables['lon'][:]
lat_ind = nearest(lats, 40).values
lon_ind = nearest(lons, 5).values
extracted_ds = ds.sel(lat=lat_ind, lon=lon_ind)

tas = extracted_ds['tas']
df = tas.to_dataframe()









#########################
### Resample / Interpolation [WIP!!!]
#########################

var_name = 'tas'
units    = 'degrees_C'

### New grid
lons_new = np.linspace(0., 5.5, 10)
lats_new = np.linspace(0., 5.5, 10)

### Original data
lons = ds.lon.values
lats = ds.lat.values
z    = ds.variables[var][0,:,:].values

### Extract region to reduce CPU time
lat_bnds, lon_bnds = [lats[0], lats[-1]], [lons[0], lons[-1]]
lat_inds = np.where((lats > lat_bnds[0]) & (lats < lat_bnds[1]))[0]
lon_inds = np.where((lons > lon_bnds[0]) & (lons < lon_bnds[1]))[0]
extracted_ds = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))

### Resampled data
interp_func = interpolate.interp2d(x, y, z, kind='linear')
znew = interp_func(xnew, ynew)

### Create a DataArray
ds1 = xr.DataArray(znew, dims=('latitude', 'longitude'), 
                         coords={'latitude': ynew, 'longitude': xnew},
                         name=var_name, attrs={'units': units} )

### Write to iris cube
cube = ds1.to_iris()
