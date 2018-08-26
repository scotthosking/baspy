import iris



def fix_cubelist_before_concat(cubelist, dataset, model, freq):


    '''
    CMIP5 Fixes to enable cubes of individual datafiles to concatenate

    '''
    if dataset == 'cmip5':

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

            for c in cubelist: c.attributes.clear()

            print('>> Applied '+model+' fixes <<')




    '''
    HAPPI
    '''
    if dataset == 'happi':

        ### fix for HAPPI MIROC monthly data to allow cubes to concatenate (e.g., All-Hist, ua, run001)
        ### --- Make this more generic for all models !!!!
        if (model == 'MIROC5') & (freq == 'mon'):
            for c in cubelist:
                coords = [dc.long_name for dc in c.dim_coords]
                for axis in coords:
                    if c.coord(axis).points.dtype == 'float64':
                        c.coord(axis).points  = c.coord(axis).points.astype('float32')
                for axis in ['time','latitude','longitude']:
                       if c.coord(axis).bounds.dtype == 'float64':
                        c.coord(axis).bounds  = c.coord(axis).bounds.astype('float32')
                if c.coord('time').units != cubelist[0].coord('time').units:
                    ### note that we have already unified time coords above.
                    c.coord('time').units = cubelist[0].coord('time').units

            print('>> Applied '+model+' fixes <<')



    return cubelist