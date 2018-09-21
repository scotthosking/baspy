import numpy as np
import sys

### Import Iris utils
from baspy import __modules
if 'iris' in __modules: from baspy._iris.util import *

'''
General python utilities (For numpy, scipy, pandas etc)

'''

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    from math import radians, cos, sin, asin, sqrt
    
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r


def lpfilter(input_signal, win):
    # Low-pass linear Filter
    # (2*win)+1 is the size of the window that determines the values that influence 
    # the filtered result, centred over the current measurement
    from scipy import ndimage
    kernel = np.lib.pad(np.linspace(1,3,win), (0,win-1), 'reflect') 
    kernel = np.divide(kernel,np.sum(kernel)) # normalise
    output_signal = ndimage.convolve(input_signal, kernel) 
    return output_signal


def get_last_modified_time_from_http_file(url):

    from six.moves import urllib
    from datetime import datetime
    from dateutil import parser

    try:
        ### Get info from http
        req = urllib.request.Request(url)
        url_handle = urllib.request.urlopen(req)
        headers = url_handle.info()

        last_modified = headers['last-modified']
        dt = parser.parse(last_modified) # datetime

        ### Convert to timestamps
        utc_naive  = dt.replace(tzinfo=None) - dt.utcoffset()
        timestamp = (utc_naive - datetime(1970, 1, 1)).total_seconds()

    except urllib.error.URLError as err:
        print('WARNING: can not access '+url)
        timestamp = -9999.

    return timestamp


def nearest_neighbour(items,my_value):
    '''
    Find the nearest_neighbour

    >>> nearest_neighbour(lats, 10.2)
    
    '''
    nearest = min(items, key=lambda x: abs(x - my_value))
    # delta   = abs(nearest - my_value)
    return nearest


def cumulative_rolling_window(arr,n):
    '''
    see https://stackoverflow.com/questions/12709853/python-running-cumulative-sum-with-a-given-window
    '''
    b = arr.cumsum()
    b[n:] = b[n:] - b[:-n]
    return b    


# End of util.py
