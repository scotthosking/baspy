import os
import numpy as np
import datetime
import os.path
import cf_units as units
import iris
from baspy import __baspy_path

root = '/group_workspaces/jasmin4/bas_climate/data/ecmwf'

### Create folder for storing data
if not os.path.exists(__baspy_path):
	os.makedirs(os.path.expanduser(__baspy_path))

def get_6hr_fnames(start_date, end_date, var_name, months='all', verbose=True):
	"""

	Get /Path/filenames for ERA-Interim files within date range

	Start and end date can be specified using a range of strings:
		e.g., '19790101', '1979-01-01', '19790101010101'

	Months, default is all months
		e.g., Months=[6,7,8]

	"""

	from dateutil import parser
	import pandas as pd

	start_datetime = parser.parse(start_date)
	end_datetime   = parser.parse(end_date)
	if verbose == True:
		print(start_datetime)
		print(end_datetime)
	
	filenames = [] # create an empty list, ready to create list of *.nc filenames
	date = start_datetime

	if months == 'all': months=range(1,13)

	### Get level_str from var_name
	level_str = None
	df_as = pd.read_csv(root+'/era-interim/era-interim_6hrly_surface_vars.csv')
	df_ap = pd.read_csv(root+'/era-interim/era-interim_6hrly_pressure_lev_vars.csv')
	if var_name in df_as['surface_vars'].values:      level_str = 'as'
	if var_name in df_ap['pressure_lev_vars'].values: level_str = 'ap'
	if level_str == None: 
		print('Surface Vars        =', df_as['surface_vars'].values)
		print('Pressure Level Vars =', df_ap['pressure_lev_vars'].values)
		raise ValueError('Can not find files for var_name='+var_name)

	### Get all filenames for all 6 hourly fields between start and end, inclusive
	while date <= end_datetime:
		yr       = str(date.year)
		mon      = str("{:0>2d}".format(date.month))
		day      = str("{:0>2d}".format(date.day))
		hr       = str("{:0>2d}".format(date.hour))
		minute   = str("{:0>2d}".format(date.minute))
		date_str = ''.join([yr,mon,day,hr,minute])
		
		file=root+'/era-interim/6hr/gg/'+level_str+'/'+yr+'/'+mon+'/'+day+'/gg'+level_str+''+date_str+'.nc'
		
		if int(mon) in months:
			filenames.append(file)
		
		# Add 6 hours to read in next file
		time_increment = datetime.timedelta(days=0, hours=6, minutes=0)
		date = date + time_increment  
	
	return filenames


def edit_erai_attributes(cube, field, filename):
	### Remove attributes from cube on read
	cube.attributes.pop('history', None)
	cube.attributes.pop('time',    None)
	cube.attributes.pop('date',    None)
	cube.attributes.pop('valid_max',    None)
	cube.attributes.pop('valid_min',    None)
	cube.coord('t').attributes.pop('time_origin', None)


def get_cube(start_date, end_date, var_name, months='all', frequency='6hr', constraints=None, verbose=True):

	"""

	Get /Path/filenames for ERA-Interim files within date range

	Start and end date can be specified using a range of strings:
		e.g., '19790101', '1979-01-01', '19790101010101'

	var_name is a constraint on the cube variable name (i.e., cube.var_name)
		e.g., var_name = 'T2'

	"""

	### To do....
	#
	# if >30 fnames then do 30 fnames at a time, and then concatenate at the end !!!!!!!!!
	#
	# change default frequency to monthly

	if frequency == '6hr': 
		fnames = get_6hr_fnames(start_date, end_date, var_name, months=months, verbose=verbose)
	
	con = iris.Constraint(cube_func=lambda cube: cube.var_name == var_name)
	
	### Additional constrains (level, time)
	if (constraints != None): con = con & constraints

	with units.suppress_errors():
		cubelist = iris.load(fnames, constraints=con, callback=edit_erai_attributes)

	### Setup new coord to add to cube (see below)
	model_coord = iris.coords.AuxCoord('ERA-Interim', long_name='Model', units='no_unit')

	### Fix cubes to all match a reference cube before we can merge
	ref_cube = cubelist[0]
	for c in cubelist: 
		c.coord('latitude').points         = ref_cube.coord('latitude').points
		c.coord('longitude').points        = ref_cube.coord('longitude').points
		c.coord('latitude').standard_name  = ref_cube.coord('latitude').standard_name
		c.coord('longitude').standard_name = ref_cube.coord('longitude').standard_name
		c.coord('t').var_name              = 'time' # To match CMIP standard 
		c.coord('t').long_name             = 'time' #
		c.add_aux_coord(model_coord)                # Add model name as a scalar coord

	iris.util.unify_time_units(cubelist)
	cube = cubelist.concatenate_cube()
	cube = iris.util.squeeze(cube)

	return cube


def get_land_mask():
	with units.suppress_errors():
		cube = iris.load_cube(root+'/era-interim/erai_invariant.nc', 'land_binary_mask')
	return cube

