from pandas import DataFrame
import baspy as bp
import xarray as xr

'''
Wishlist for baspy v2:
    * include capability to use Xarray in addition to Iris
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

### New grid
lons_new     = np.linspace(0., 5.5, 10)
lats_new     = np.linspace(0., 5.5, 10)
nlons, nlats = len(lons_new), len(lats_new)

### Original grid
lons = ds[var_name].lon.values
lats = ds[var_name].lat.values

### Extract region to reduce CPU time
lat_bnds, lon_bnds = [lats_new[0], lats_new[-1]], [lons_new[0], lons_new[-1]]
lat_inds = np.where((lats > lat_bnds[0]) & (lats < lat_bnds[1]))[0]
lon_inds = np.where((lons > lon_bnds[0]) & (lons < lon_bnds[1]))[0]
extracted_ds = ds.sel(lat=slice(*lat_bnds), lon=slice(*lon_bnds))

### Resampled data
znew = np.zeros( (ntime, nlons, nlats) )
for t in range(0,XXX):
    z    = ds[var_name][t,:,:].values
    interp_func = interpolate.interp2d(lons, lats, z, kind='linear')
    znew[t,:,:] = interp_func(xnew, ynew) # Transpose (t,y,x)??

### Create a DataArray
ds1 = xr.DataArray(znew, dims=('latitude', 'longitude'), 
                         coords={'latitude': lats_new, 'longitude': lons_new},
                         name=var_name, attrs={'units': ds[var_name].units} )

### Write to iris cube
cube = ds1.to_iris()
