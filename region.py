'''

To extract a region:
>>> bounds = bp.region.china
>>> cube   = bp.region.extract(cube, bounds)

'''


###############################
### Pre-defined named locations
###############################
class City:
    london = { 'lon':0.739,   'lat':51.3026 }
    mumbai = { 'lon':72.4933, 'lat':18.5830 }


###############################
### Pre-defined regional bounds
###############################

nh               = {'lat_bnds':(0, 90)   }
sh               = {'lat_bnds':(-90, 0)  }
arctic_circle    = {'lat_bnds':(66, 90)  }
antarctic_60_90S = {'lat_bnds':(-90, -60)}
mid_latitudes    = {'lat_bnds':(-60, 78) } # to leave off the poles from plots

class Continent: 
    europe               = {'lon_bnds':(-11.25, 33.75), 'lat_bnds':(35.1, 72.5) }
    noth_atlantic_europe = {'lon_bnds':(-50., 33.75),   'lat_bnds':(25.0, 72.5) }

class Country:
    uk     = {'lon_bnds':(-11, 2), 'lat_bnds':(48, 60) }
    france = {'lon_bnds':(-5, 9),  'lat_bnds':(41, 52) }
    spain  = {'lon_bnds':(-11, 6), 'lat_bnds':(35, 45) }
    egypt  = {'lon_bnds':(22, 39), 'lat_bnds':(20, 34) }
    china  = {'lon_bnds':(72,135), 'lat_bnds':(20,55)  }

class Sub_regions:
    central_england = {'lon_bnds':(-3.5, 0.), 'lat_bnds':(51.5, 53.5) }
    himalayas       = {'lon_bnds':(60, 100),  'lat_bnds':(15, 45)     }


###############################
### Definitions
###############################

def extract(cube, bounds):

    '''
    Extract region using pre-defined lat/lon bounds

    >>> bounds = bp.region.china
    >>> cube   = bp.region.extract(cube, bounds)
    '''

    keys = bounds.keys()

    if ('lon_bnds' in keys) | ('lat_bnds' in keys):

        if ('lon_bnds' in keys) & ('lat_bnds' in keys):
            cube = cube.intersection( longitude=bounds['lon_bnds'], latitude=bounds['lat_bnds'] )

        if ('lon_bnds' in keys) & ('lat_bnds' not in keys):
            cube = cube.intersection( longitude=bounds['lon_bnds'] )

        if ('lon_bnds' not in keys) & ('lat_bnds' in keys):
            cube = cube.intersection( latitude=bounds['lat_bnds'] )

    else:

        raise ValueError('Need to define lon_bnds and/or lat_bnds')

    return cube

