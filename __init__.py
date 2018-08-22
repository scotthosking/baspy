"""
BASpy is essentially a collection of wrappers around the 
Python package "Iris" (at least it is at the moment...)

Iris 
------
Homepage:  http://scitools.org.uk/iris/
Reference: http://scitools.org.uk/iris/docs/latest/iris/iris.html
Code:      https://github.com/SciTools/iris
Forums:	   https://groups.google.com/forum/#!forum/scitools-iris

BASpy
------
Created by:   Scott H

"""

import os
import iris

### BASpy version number
__version__ = "0.7"

### Place to store catalogues and example data
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))

### For sharing catalogues between users
__catalogues_url = "http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/"
__catalogues_dir = "/group_workspaces/jasmin4/bas_climate/public/files/baspy/"

# Import modules
import baspy.util
import baspy._catalogue
import baspy._get_cubes
import baspy.erai

### Link modules for easier access (e.g., baspy.get_cubes() )
get_cubes   = baspy._get_cubes.get_cubes
get_cube    = baspy._get_cubes.get_cube
catalogue   = baspy._catalogue.catalogue
eg_cube     = baspy.util.eg_cube
eg_cubelist = baspy.util.eg_cubelist


