"""
BASpy is essentially a collection of tools for working with
large climate model data. For the most part it is a wrapper around the 
Python package "Iris" although the plan is to do more with Xarray.

Iris 
------
Homepage:  http://scitools.org.uk/iris/
Reference: http://scitools.org.uk/iris/docs/latest/iris/iris.html
Code:      https://github.com/SciTools/iris
Forums:	   https://groups.google.com/forum/#!forum/scitools-iris


Xarray
------
Homepage:  http://xarray.pydata.org/en/stable/


BASpy
------
Created by:   Scott Hosking
Contributors: Tom Bracegirdle, Tony Phillips

"""

# Import modules
import os
import baspy._catalogue
import baspy.util
import baspy._iris._get_cubes
import baspy._iris.erai


### BASpy version number
__version__ = "0.9"

### Place to store catalogues and example data
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))

### For sharing catalogues between users
__catalogues_url = "http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/"
__catalogues_dir = "/group_workspaces/jasmin4/bas_climate/public/files/baspy/"


##################################
### Create shortcuts for easier access 
###   e.g., baspy.get_cubes()
##################################

### General
catalogue   = baspy._catalogue.catalogue

### Iris specific
eg_cube     = baspy._iris.util.eg_cube
eg_cubelist = baspy._iris.util.eg_cubelist
get_cubes   = baspy._iris._get_cubes.get_cubes
get_cube    = baspy._iris._get_cubes.get_cube
baspy.erai  = baspy._iris.erai
