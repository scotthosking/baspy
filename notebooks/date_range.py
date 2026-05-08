import glob
import re
import pandas as pd
import os
import numpy as np

filename_structure = 'Var_CMOR_Model_Experiment_RunID_StartDate-EndDate'

netcdfs = ['tasmax_Aday-ISIMIP2b_CAM4-2degree_Plus20-Future_CMIP5-MMM-est1_v1-0_run001_19990101-20091231.nc4', 
			'tasmax_Aday-ISIMIP2b_CAM4-2degree_Plus20-Future_CMIP5-MMM-est1_v1-0_run001_20100101-20191231.nc4' ]

start_date = 19990102
end_date   = 21240102




def get_file_date_ranges(fnames, filename_structure):
    ### Get start and end dates from file names
    ind = filename_structure.split('_').index('StartDate-EndDate')
    start_dates, end_dates = np.array([]), np.array([])

    for fname in list(fnames):

        fname = os.path.splitext(fname)[0] # rm extention

        ### Is this file time-varying?
        if '_fx_' in fname:
            ### Fixed variable (e.g., land-mask)
            start_date, end_date = 0, 0

        else:
            ### Time-varying (e.g., temperature)
            date_str = fname.split('_')[ind].split('-')

            ### Interpreting the dates
            if len(date_str) == 2:
                ### e.g.,'19900101-20000101'
                start_date, end_date = int(date_str[0]), int(date_str[1])

            elif (len(date_str) == 3):
                if (date_str[2] == 'clim'):
                    ### e.g.,'186001-187912-clim'
                    ### see /badc/cmip5/data/cmip5/output1/MOHC/HadGEM2-ES/piControl/mon/atmos/Amon/r1i1p1/latest/pfull
                    start_date, end_date = int(date_str[0]+'01'), int(date_str[1]+'31')
                else:
                    print('Cannot identify dates '+fname)

            elif (len(date_str) == 1) & (int(date_str[0]) >= 1800) & (int(date_str[0]) <= 2300):
                ### e.g., '1990'
                ### see /badc/cmip5/data/cmip5/output1/ICHEC/EC-EARTH/amip/subhr/atmos/cfSites/r3i1p1/latest/ccb
                start_date, end_date = int(date_str[0]), int(date_str[0])

            else:
                ### Can't define date
                ###### To do: if no date_range then get from ncdump? !!
                print('Cannot identify dates '+fname)
                start_date, end_date = np.nan, np.nan

        start_dates = np.append( start_dates, start_date )
        end_dates   = np.append( end_dates,   end_date )   

    return start_dates, end_dates






### List file names that appear to be within our date range
if (start_date != None) | (end_date != None):
	file_date_range = get_file_date_ranges(netcdfs, filename_structure)
	if (start_date == None): start_date = np.min(file_date_range[0])
	if (end_date == None):   end_date   = np.max(file_date_range[1])

	keep_ind1 = np.where( (end_date >= file_date_range[0])   & (end_date <= file_date_range[1])   )[0]
	keep_ind2 = np.where( (start_date >= file_date_range[0]) & (start_date <= file_date_range[1]) )[0]
	keep_ind  = np.sort(np.unique(np.append(keep_ind1,keep_ind2)))
	
	if (len(keep_ind) == 0): 
		raise ValueError("No netcdf files within requested date range")
	else:
		netcdfs = np.array(netcdfs)[keep_ind]

print(netcdfs) # TMP!!!