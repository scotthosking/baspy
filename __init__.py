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

# from baspy import (util,cmip5,erai,upscale)

import baspy.util
import baspy._catalogue
import baspy._get_cubes

import baspy.cmip5
import baspy.erai
import baspy.upscale

### BASpy version number
__version__ = "0.5"


get_cubes   = baspy._get_cubes.get_cubes
get_cube    = baspy._get_cubes.get_cube
catalogue   = baspy._catalogue.catalogue
eg_cube     = baspy.util.eg_cube
eg_cubelist = baspy.util.eg_cubelist