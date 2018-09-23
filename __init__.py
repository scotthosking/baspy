"""
BASpy is essentially a collection of tools for working with
large climate model data. For the most part it is a wrapper around the 
Python package "Iris" although the plan is to do more with Xarray.

Iris 
------
Homepage:  http://scitools.org.uk/iris/
Reference: http://scitools.org.uk/iris/docs/latest/iris/iris.html
Code:      https://github.com/SciTools/iris
Forums:    https://groups.google.com/forum/#!forum/scitools-iris


Xarray
------
Homepage:  http://xarray.pydata.org/en/stable/


BASpy
------
Created by:   Scott Hosking
Contributors: Tom Bracegirdle, Tony Phillips

"""

import os, sys

### BASpy version number
__version__ = "0.9"

### Place to store catalogues and example data
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))

### For sharing catalogues between users
__catalogues_url = "http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/"
__catalogues_dir = "/group_workspaces/jasmin4/bas_climate/public/files/baspy/"


###############
### Setup BASpy
###############

### Optional Libraries
try:
    import iris
except ImportError:
    # Iris is not installed
    pass

try:
    import xarray
except ImportError:
    # Xarray is not installed
    pass

__modules = sys.modules # must come before import baspy.util

### General Libraries
from . import util
from . import region
from . import _catalogue
catalogue = _catalogue.catalogue
get_files = _catalogue.get_files

### Set up wrappers for iris, xarray etc
if 'iris' in __modules:
    from . import _iris
    eg_cube     = _iris.util.eg_cube
    eg_cubelist = _iris.util.eg_cubelist
    get_cubes   = _iris.get_cubes.get_cubes
    get_cube    = _iris.get_cubes.get_cube
    erai        = _iris.erai

if 'xarray' in __modules:
    from . import _xarray as XR

