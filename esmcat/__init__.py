"""
ESMcat is a collection of tools for working with large climate model data.

Xarray
------
Homepage:  http://xarray.pydata.org/en/stable/


ESMcat
------
Created by:   Scott Hosking
Contributors: Tom Bracegirdle, Tony Phillips

"""

import os, json as _json

### ESMcat version number
__version__ = "1.9"

### Place to store catalogues and example data
__esmcat_path = os.path.expanduser("~/.esmcat")
if not os.path.exists(__esmcat_path):
    os.makedirs(os.path.expanduser(__esmcat_path))


###############
### Config
###############

def get_config():
    """Return the current esmcat config from ~/.esmcat/config.json."""
    config_file = os.path.join(__esmcat_path, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as _f:
            return _json.load(_f)
    return {}

def set_config(machine):
    """
    Set the machine name in ~/.esmcat/config.json.
    esmcat will load datasets_{machine}.json from the package directory.
    e.g. ecat.set_config('jasmin')
    """
    config_file = os.path.join(__esmcat_path, 'config.json')
    config = get_config()
    config['machine'] = machine
    with open(config_file, 'w') as _f:
        _json.dump(config, _f, indent=4)
    print("Config saved: machine='" + machine + "'")
    print("Restart Python for the change to take effect.")


from . import catalogue as _catalogue_module
catalogue = _catalogue_module.catalogue
get_files = _catalogue_module.get_files

try:
    import xarray as _xr
except ImportError:
    _xr = None

if _xr is not None:
    def open_dataset(df):
        files = get_files(df)
        if len(files) == 1:
            return _xr.open_dataset(files[0])
        return _xr.open_mfdataset(files)

