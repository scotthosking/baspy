"""
BASpy is a collection of tools for working with large climate model data.

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
__version__ = "1.1"

### Place to store catalogues and example data
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))

### For sharing catalogues between users
__catalogues_url = "http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/"
__catalogues_dir = "/gws/nopw/j04/bas_climate/public/files/baspy/"


###############
### Setup BASpy
###############

### Optional Libraries
try:
    import xarray
except ImportError:
    # Xarray is not installed
    pass

__modules = sys.modules

### General Libraries
from . import _catalogue
catalogue = _catalogue.catalogue
get_files = _catalogue.get_files

### Set up wrappers for xarray etc
if 'xarray' in __modules:
    from . import _xarray
    eg_Dataset   = _xarray.util.eg_Dataset
    eg_DataArray = _xarray.util.eg_DataArray
    open_dataset = _xarray.open_dataset

