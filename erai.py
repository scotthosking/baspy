#!/usr/bin/python
# Filename: erai.py

import os
import numpy as np
import re
import datetime
import glob, os.path

import baspy as bp
import iris
import iris.coords as coords

### Create folder for storing data
baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(baspy_path):
	os.makedirs(os.path.expanduser(baspy_path))


def get_fnames(start_date, end_date, level_str):
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

# End of erai.py
