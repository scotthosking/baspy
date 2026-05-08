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

import os, json as _json

### BASpy version number
__version__ = "1.9"

### Place to store catalogues and example data
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path):
    os.makedirs(os.path.expanduser(__baspy_path))


###############
### Config
###############

def get_config():
    """Return the current baspy config from ~/.baspy/config.json."""
    config_file = os.path.join(__baspy_path, 'config.json')
    if os.path.exists(config_file):
        with open(config_file) as _f:
            return _json.load(_f)
    return {}

def set_config(machine):
    """
    Set the machine name in ~/.baspy/config.json.
    baspy will load datasets_{machine}.json from the package directory.
    e.g. bp.set_config('jasmin')
    """
    config_file = os.path.join(__baspy_path, 'config.json')
    config = get_config()
    config['machine'] = machine
    with open(config_file, 'w') as _f:
        _json.dump(config, _f, indent=4)
    print("Config saved: machine='" + machine + "'")
    print("Restart Python for the change to take effect.")


from . import catalogue as _catalogue_module
catalogue = _catalogue_module.catalogue
get_files = _catalogue_module.get_files

