import numpy as np
import iris
import iris.coord_categorisation


def cube_trend(cube, var_name=None, time_coord=None):

	'''
	Currently this def for calculating trends should only be used for year-to-year cubes.
	e.g.,
		* A cube where each timeframe represents annual means 
		* A cube where each timeframe represents seasonal means (one season per year)

	Note: this definition will be replaced at some point with one that Tony is writing.
	'''

	from scipy import stats
	import iris.coords as coords

	lons, lats = cube.coord('longitude').points, cube.coord('latitude').points

	### Define years for trend analysis
	years = []
	if len(cube.coords('year')) > 0:        years = cube.coord('year').points
	if len(cube.coords('season_year')) > 0: years = cube.coord('season_year').points
	if len(years) == 0:
		raise ValueError("Need to assign either 'year' or 'season_year' as Auxiliary coordinates to cube")

	### Collapse cube to correctly assign time bounds in output metadata
	if (time_coord == None): time_coord = 'time'
	cube2 = cube.collapsed(time_coord, iris.analysis.MEAN)

	slope, p_value = iris.cube.copy.deepcopy(cube2), iris.cube.copy.deepcopy(cube2)
	slope.data[:,:], p_value.data[:,:] = np.nan, np.nan

	slope.rename(var_name+'_trend')
	p_value.rename(var_name+'_trend_sig')

	slope.units = str(slope.units)+' yr-1'
	p_value.units = '1'

	for x in range(0,len(lons)):
		for y in range(0,len(lats)):
			slope.data[y,x], intercept, r_value, p_value.data[y,x], std_err = stats.linregress( years, cube.data[:,y,x] )

	return slope, p_value


def months2seasons(cube, seasons=None):

	import iris.coord_categorisation

	### to-do: Add check that cube is monthly!!!!!!!!! 

	### Create seasonal means (unique and specified 3-month seasons)
	if (seasons == None):
	   seasons=['mam', 'jja', 'son', 'djf']
	if len(cube.coords('clim_season')) == 0:
	   iris.coord_categorisation.add_season(cube, 'time', name='clim_season', seasons=seasons)
	if len(cube.coords('season_year')) == 0:
	   iris.coord_categorisation.add_season_year(cube, 'time', name='season_year', seasons=seasons)

	# Keep only those times where we can produce seasonal means using exactly 3 months
	# (i.e., remove times from cubelist where only 1 or 2 times exist for that season)
	clim_seasons = cube.coords('clim_season')[0].points
	season_years = cube.coords('season_year')[0].points
	ntimes = len(cube.coords('time')[0].points)

	keep_ind = np.zeros((0), dtype=np.int)
	for i in range(0,ntimes):
	   ind = np.where( (clim_seasons == clim_seasons[i]) & (season_years == season_years[i]) )[0]
	   n_months_in_season = len(clim_seasons[i]) # length of string, usually 3 (e.g., 'djfm' = 4)
	   if (len(ind) == n_months_in_season): keep_ind = np.append(keep_ind,i)
	cube = cube[keep_ind]

	seasons = cube.aggregated_by(['clim_season', 'season_year'], iris.analysis.MEAN)
	return seasons



def months2annual(cube):

	import iris.coord_categorisation

	### to-do: Add check that cube is monthly!!!!!!!!! 

	if len(cube.coords('year')) == 0:
	   iris.coord_categorisation.add_year(cube, 'time', name='year')

	if len(cube.coords('month')) == 1:       cube.remove_coord('month')
	if len(cube.coords('clim_season')) == 1: cube.remove_coord('clim_season')
	if len(cube.coords('season_year')) == 1: cube.remove_coord('season_year')

	### Keep only those times where we can produce annual means using exactly 12 months
	years = cube.coords('year')[0].points
	ntimes = len(cube.coords('time')[0].points)

	keep_ind = np.zeros((0), dtype=np.int)
	for i in range(0,ntimes):
	   ind = np.where( (years == years[i]) )[0]
	   n_months_in_year = 12
	   if (len(ind) == n_months_in_year): keep_ind = np.append(keep_ind,i)
	cube = cube[keep_ind]

	annual = cube.aggregated_by(['year'], iris.analysis.MEAN)
	return annual


def unify_similar_grid_coords(cubes, cube_template=None):
	"""
	If the x or y coordinates are similar but different from a template cube then make them the same.
	If cube_template is not specified then default to the first cube in the cubelist.
	
	Examples:
		cubelist = bp.util.unify_similar_grid_coords(cubelist)
		cubes = bp.util.unify_similar_grid_coords(cubes, cube_template=cubes[0])
	"""

	if (type(cubes) == iris.cube.Cube):
		cubes = iris.cube.CubeList([cubes])

	if (cube_template == None):
		cube_template = cubes[0]

	if (type(cube_template) != iris.cube.Cube):
		raise ValueError('cube_template is not a cube')
	
	if len(cubes) > 0:
		for i, cube in enumerate(cubes):
			for axis in ['X', 'Y']:
				if (np.any(cube.coord(axis=axis).points != cube_template.coord(axis=axis).points) and
						np.all(np.isclose(cube.coord(axis=axis).points, cube_template.coord(axis=axis).points))):
						cube.coord(axis=axis).points = cube_template.coord(axis=axis).points
						cubes[i] = cube
				if (np.any(cube.coord(axis=axis).bounds != cube_template.coord(axis=axis).bounds) and
						np.all(np.isclose(cube.coord(axis=axis).bounds, cube_template.coord(axis=axis).bounds))):
						cube.coord(axis=axis).bounds = cube_template.coord(axis=axis).bounds
						cubes[i] = cube

	return cubes



def rm_time_overlaps(cubelist):
	"""
	Remove time overlaps from a cubelist
	keeping the duplicated period from the cube that
	comes first within the cubelist
	"""	
	if (cubelist.__class__ != iris.cube.CubeList):
		raise ValueError('rm_time_overlaps requires a cubelist')
	
	if (len(cubelist) == 1): return cubelist
	
	### Check that all cubes have the same var_name
	var_names = [c.var_name for c in cubelist]
	all_same = all(x==var_names[0] for x in var_names)
	if all_same == False:
		raise ValueError('cubelist contains cubes with difference var_names')
	
	### Unify time coordinates to identify overlaps
	iris.util.unify_time_units(cubelist)
	
	### Sort cubelist by start time
	cubelist.sort(key=lambda cube: cube.coord(axis='t').points[0])
	### Tony: potentially a more robust robust solution??
	### cubelist.sort(key=lambda cube: cube.coord(axis='t').units.num2date(cube.coord(axis='t').points[0]))


	i = 1
	while i < len(cubelist):

		max1 = np.max(cubelist[i-1].coord(axis='t').points)
		min2 = np.min(cubelist[i].coord(axis='t').points)
		
		if (min2 <= max1):
			print('>>> WARNING: Removing temporal overlaps'
					' from cubelist <<<')
			print(min2, max1)
			with iris.FUTURE.context(cell_datetime_objects=False):
				con = iris.Constraint(time=lambda t: t > max1)
				cubelist[i] = cubelist[i].extract(con)

		if (cubelist[i].__class__ != iris.cube.Cube):
			cubelist.pop(i)
		else:
			i = i + 1
	
	return cubelist


def eg_cube():
	""" 
	Load an example cube
	"""
	cmip5_dir = '/badc/cmip5/data/cmip5/output1/'
	cube = iris.load_cube(cmip5_dir + 
			'MOHC/HadGEM2-A/amip/mon/atmos/Amon/r1i1p1/latest/'
			'tas/tas_Amon_HadGEM2-A_amip_r1i1p1_197809-200811.nc')
	return cube


def eg_cubelist():
	"""
	Load an example cubelist
	"""
	cmip5_dir = '/badc/cmip5/data/cmip5/output1/'
	cubelist = iris.load(
			[cmip5_dir+'MOHC/HadGEM2-A/amip/mon/atmos/Amon/r1i1p1/latest/'
			'psl/psl_Amon_HadGEM2-A_amip_r1i1p1_197809-200811.nc', 
			cmip5_dir +'MOHC/HadGEM2-A/amip/mon/atmos/Amon/r1i1p1/latest/'
			'tas/tas_Amon_HadGEM2-A_amip_r1i1p1_197809-200811.nc']
			)
	return cubelist






def make_ts_cube(ts, cube, rename=None, units=None):
	'''
	Make a 1D time-series cube based on another cube with the same time coordinate system

	add_scalar_coords: 
		see bp.util.add_scalar_coords def for more info

	'''

	### Setup new name, units etc (default is to keep the same)
	if (rename != None): cube.rename(rename)
	if (units == None): units=cube.units
	long_name=cube.long_name

	new_cube = iris.cube.Cube( np.zeros(ts.shape), long_name=long_name, units=units )

	### Copy time coordinates and all attributes from original cube	to new cube
	t_coord = cube.coord(axis='t')
	new_cube.add_dim_coord(t_coord, 0)

	for coord in cube.aux_coords: 
		if len(coord.points) == 1: data_dims=None
		if len(coord.points) == len(t_coord.points): data_dims=0 ### Generalise this!!!!!!!!!!!!!!!!
		new_cube.add_aux_coord(coord, data_dims=data_dims)

	new_cube.attributes = cube.attributes

	### Remove mask if present and unneeded
	if type(ts) == np.ma.core.MaskedArray:
		if all(ts.mask == False): ts = ts.data

	### Copy time series into new cube
	new_cube.data = ts
	
	return new_cube
	

def add_scalar_coords(cube, coord_dict=None):
	'''
	Useful for adding, e.g., longitude and latitude to a 1D time series cube at a specific location

	coord_dict needs to be a dictionary of the form:
		{'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}"

	'''

	if (type(coord_dict) != dict):
		raise ValueError("coord_dict needs to be a dictionary of the form: \
							{'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}")

	import iris.coords as coords

	for key, values in coord_dict.iteritems():

		if (type(values) != list) | (len(values) != 2):
			ValueError("coord_dict must of the form: {'key1': ['scalar1', 'units1'], 'key2': ['scalar2', 'units2']}")
		
		scalar = values[0]
		units  = values[1]
		new_coord = coords.AuxCoord(scalar, long_name=key, units=units)
		cube.add_aux_coord(new_coord)

	return cube


# End of util.py