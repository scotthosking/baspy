import iris



def fix_cubelist_before_concat(cubelist, dataset, my_dict):



    '''
    CMIP6
    '''
    if dataset == 'cmip6':

        model = my_dict['Model']

        ### MCM-UA-1-0 uses non-standard var_names for x/y coords (rename these)
        if (model == 'MCM-UA-1-0'):
            for cube in cubelist:
                var_names = [dim_coords.var_name for dim_coords in cube.dim_coords]
                for var_name in var_names:
                    if var_name == 'latitude':  cube.coord(var_name).var_name = 'lat'
                    if var_name == 'longitude': cube.coord(var_name).var_name = 'lon'

            print('>> Applied '+model+' fixes <<')


    '''
    CMIP5 Fixes to enable cubes of individual datafiles to concatenate

    '''
    if dataset == 'cmip5':

        model = my_dict['Model']
        freq  = my_dict['Frequency']
        exp   = my_dict['Experiment']

        ### Fix EC-Earth
        ### turn Gregorian calendars into standard ones
        ### !!! assumes that the dates are actually the same in Gregorian and standard calendar
        ### (this is definitely true for historical and RCP runs)
        if (model == 'EC-EARTH'):
            if ( (exp.startswith('rcp')) | (exp.startswith('hist')) ):
                # fix calendar
                for cube in cubelist:
                    for time_coord in cube.coords():
                        if time_coord.units.is_time_reference():
                            if time_coord.units.calendar == u'gregorian':
                                time_coord.units = cf_units.Unit(time_coord.units.origin, u'standard')

            # promote auxiliary time coordinates to dimension coordinates
            for cube in cubelist:
                for time_coord in cube.coords():
                    if time_coord.units.is_time_reference():
                        if (time_coord in cube.aux_coords and time_coord not in cube.dim_coords):
                            iris.util.promote_aux_coord_to_dim_coord( cube, time_coord )

            iris.util.unify_time_units(cubelist)

            # remove long_name from all time units
            for cube in cubelist:
                for time_coord in cube.coords():
                    if time_coord.units.is_time_reference():
                        time_coord.long_name = None

            for cube in cubelist: cube.attributes.clear()

            print('>> Applied '+model+' fixes <<')




    '''
    HAPPI
    '''
    if dataset == 'happi':

        model = my_dict['Model']
        freq  = my_dict['Frequency']
        exp   = my_dict['Experiment']

        ### fix for HAPPI MIROC monthly data to allow cubes to concatenate (e.g., All-Hist, ua, run001)
        ### --- Make this more generic for all models !!!!
        if (model == 'MIROC5') & (freq == 'mon'):
            for cube in cubelist:
                coords = [dim_coords.standard_name for dim_coords in cube.dim_coords]
                for axis in coords:
                    if cube.coord(axis).points.dtype == 'float64':
                        cube.coord(axis).points  = cube.coord(axis).points.astype('float32')
                for axis in ['time','latitude','longitude']:
                       if cube.coord(axis).bounds.dtype == 'float64':
                        cube.coord(axis).bounds  = cube.coord(axis).bounds.astype('float32')
                if cube.coord('time').units != cubelist[0].coord('time').units:
                    ### note that we have already unified time coords before applying fix.
                    cube.coord('time').units = cubelist[0].coord('time').units

            print('>> Applied '+model+' fixes <<')



    return cubelist