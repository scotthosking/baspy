#!/usr/bin/python
# Filename: erai.py

import os
import numpy as np
import datetime
import os.path
import cf_units as units
import iris

### Create folder for storing data
baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(baspy_path):
	os.makedirs(os.path.expanduser(baspy_path))


def get_6hr_fnames(start_date, end_date, level_str):
	"""
	Get /Path/filenames for ERA-Interim files within date range
	level_str for JASMIN:
		'as' surface variables
		'ap' pressure level variables
	"""
	start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d_%H%M')
	end_datetime   = datetime.datetime.strptime(end_date,  '%Y-%m-%d_%H%M')
	
	filenames = [] # create an empty list, ready to create list of *.nc filenames
	date = start_datetime
	
	### Get all filenames for all 6 hourly fields between start and end, inclusive
	while date <= end_datetime:
		yr       = str(date.year)
		mon      = str("{:0>2d}".format(date.month))
		day      = str("{:0>2d}".format(date.day))
		hr       = str("{:0>2d}".format(date.hour))
		minute   = str("{:0>2d}".format(date.minute))
		date_str = ''.join([yr,mon,day,hr,minute])
		
		file = '/badc/ecmwf-era-interim/data/gg/as/'+yr+'/'+mon+'/'+day+'/ggas'+date_str+'.nc'
		
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
    cube.coord('t').attributes.pop('time_origin', None)


def get_cube(start_date, end_date, level_str, frequency='6hr', constraints=None):

	"""
	Get /Path/filenames for ERA-Interim files within date range
	level_str for JASMIN:
		'as' surface variables
		'ap' pressure level variables
	"""

	### Reference cube to standarise coordinate points/names etc
	if frequency == '6hr': ref_nc = '/badc/ecmwf-era-interim/data/gg/as/1979/01/01/ggas197901010000.nc'

	with units.suppress_errors():
		ref_cube = iris.load_cube(ref_nc, constraints=constraints, callback=edit_erai_attributes)

	### To do....
	#
	# if >30 fnames then do 30 fnames at a time, and then concatenate at the end !!!!!!!!!
	#
	# change default frequency to monthly

	if frequency == '6hr': fnames = get_6hr_fnames(start_date, end_date, level_str)
	
	with units.suppress_errors():
		cubelist = iris.load(fnames, constraints=constraints, callback=edit_erai_attributes)

	### Fix cubes to all match a reference cube before we can merge

	for c in cubelist: 
		c.coord('latitude').points         = ref_cube.coord('latitude').points
		c.coord('longitude').points        = ref_cube.coord('longitude').points
		c.coord('latitude').standard_name  = ref_cube.coord('latitude').standard_name
		c.coord('longitude').standard_name = ref_cube.coord('longitude').standard_name
		c.coord('t').var_name              = ref_cube.coord('t').var_name

	iris.util.unify_time_units(cubelist)
	cube = cubelist.concatenate_cube()
	cube = iris.util.squeeze(cube)

	return cube


def get_land_mask():
	with units.suppress_errors():
		cube = iris.load_cube('/group_workspaces/jasmin/bas_climate/data/ecmwf1/era-interim/erai_invariant.nc', 'land_binary_mask')
	return cube



# End of erai.py
