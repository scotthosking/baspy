import iris
import numpy as np
from numpy import ma

'''

Useful Info:
* http://ccafs-climate.org/downloads/docs/BC_methods_explaining_v2_jrv.pdf

To do:
* Add option (default?) to detrend first then add trend back-on to result

'''


def _time_mean(cube):
    time_coord = cube.coord(axis='t').name()
    return cube.collapsed(time_coord, iris.analysis.MEAN)

def _time_std(cube):
    time_coord = cube.coord(axis='t').name()
    return cube.collapsed(time_coord, iris.analysis.STD_DEV)

def _create_cube(arr, template_cube, deepcopy=True, add_attr=None):
    
    if deepcopy == True:
        cube = iris.cube.copy.deepcopy(template_cube)
    else:
        cube = template_cube

    ### Convert arr to masked_array
    if (type(template_cube.data) == np.ma.core.MaskedArray) & \
               (type(arr) == np.ndarray) :
        arr = ma.masked_array(arr, mask=cube.data.mask)

    ### Insert data into cube
    if type(template_cube.data) == type(arr): 
        cube.data = arr
    else:
        raise ValueError('unsure how to insert arr into cube')

    if type(add_attr) == dict: cube.attributes.update(add_attr)

    return cube




def bias_correction(Obs_ref, Sim_ref, Sim_fut):

    ### Regrid
    Sim_ref = Sim_ref.regrid( Obs_ref, iris.analysis.Linear() )
    Sim_fut = Sim_fut.regrid( Obs_ref, iris.analysis.Linear() )

    ### Should we detrend first then add the trend back on?? !!!!!!!!!!!

    ### Create mean over whole period from daily data
    Obs_ref_mean = _time_mean(Obs_ref)
    Sim_ref_mean = _time_mean(Sim_ref)
    Sim_fut_mean = _time_mean(Sim_fut)
    Obs_ref_std  = _time_std(Obs_ref)
    Sim_ref_std  = _time_std(Sim_ref)
    Sim_fut_std  = _time_std(Sim_fut)

    sh, bc = np.zeros(Sim_fut.data.shape), np.zeros(Sim_fut.data.shape)

    ####################
    ### bias correction
    ####################

    ### Shift (mean correction)
    sh = Sim_fut.data + (Obs_ref_mean.data - Sim_ref_mean.data)

    ### bias correction (mean & variance correction)
    bc = Obs_ref_mean.data + (Obs_ref_std.data / Sim_ref_std.data) * (Sim_fut.data - Sim_ref_mean.data)

    ######################
    ## Create cube using np arr + add attributes
    ######################

    sh = _create_cube(sh, Sim_fut, add_attr={'Calibration':'Shift'})
    bc = _create_cube(bc, Sim_fut, add_attr={'Calibration':'Bias Correction'})

    return sh, bc




def change_factor(Obs_ref, Sim_ref, Sim_fut):

    ### Regrid
    Sim_ref = Sim_ref.regrid( Obs_ref, iris.analysis.Linear() )
    Sim_fut = Sim_fut.regrid( Obs_ref, iris.analysis.Linear() )

    ### Should we detrend first then add the trend back on?? !!!!!!!!!!!

    ### Create mean over whole period from daily data
    Obs_ref_mean = _time_mean(Obs_ref)
    Sim_ref_mean = _time_mean(Sim_ref)
    Sim_fut_mean = _time_mean(Sim_fut)
    Obs_ref_std  = _time_std(Obs_ref)
    Sim_ref_std  = _time_std(Sim_ref)
    Sim_fut_std  = _time_std(Sim_fut)

    delta, cf = np.zeros(Obs_ref.data.shape), np.zeros(Obs_ref.data.shape)

    ####################
    ### change factor
    ####################

    ### Delta (mean correction)
    delta = Obs_ref.data + (Sim_fut_mean.data - Sim_ref_mean.data)

    ### change factor (mean & variance correction)
    cf = Sim_fut_mean.data + (Sim_fut_std.data / Sim_ref_std.data) * (Obs_ref.data - Sim_ref_mean.data)

    ######################
    ## Create cube using np arr + add attributes
    ######################

    delta = _create_cube(delta, Obs_ref, add_attr={'Calibration':'Delta'})
    cf    = _create_cube(cf,    Obs_ref, add_attr={'Calibration':'Change Factor'})

    return delta, cf





'''

Quantile Mapping (qm)

'''


def qm_bias_correction(obs_ref, sim_ref, sim_fut):

    '''
    Quanile Mapping - Bias Correction

    '''

    from scipy.stats import percentileofscore

    ### Regrid
    sim_ref = sim_ref.regrid( obs_ref, iris.analysis.Linear() )
    sim_fut = sim_fut.regrid( obs_ref, iris.analysis.Linear() )

    bias_correction = np.zeros(sim_fut.data.shape)

    ### Identify time axis (usually first dim)
    time_coord = sim_fut.coord(axis='t').name()
    coords = [coord.name() for coord in sim_fut.dim_coords]
    time_axis = coords.index(time_coord)

    ### Loop over non-time indices (usually lat and lon)
    collapsed_cube = sim_fut.collapsed(time_coord, iris.analysis.MEAN)

    for xy_ind in np.ndindex(collapsed_cube.shape):
        t_slice = (xy_ind[:time_axis] + (slice(None),) + xy_ind[time_axis:]) # e.g., (slice(None, None, None), 1, 1)
        
        ### Bias Correcting by Quantile Mapping
        for i, val in enumerate(sim_fut.data[t_slice]):
            percentile = percentileofscore(sim_fut.data[t_slice], val)
            bias = np.percentile(obs_ref.data[t_slice], percentile) - np.percentile(sim_ref.data[t_slice], percentile)
            tyx_ind = (xy_ind[:time_axis] + (i,) + xy_ind[time_axis:]) # e.g., (2699, 1, 1)
            bias_correction[tyx_ind] = val + bias

    ### Add attribute for calibration method
    bias_correction = _create_cube(bias_correction, sim_fut, 
                            add_attr={'Calibration':'Bias Correction by Quantile Mapping'})

    return bias_correction 



def qm_change_factor(obs_ref, sim_ref, sim_fut):

    '''
    Quanile Mapping - Change Factor
    
    '''

    from scipy.stats import percentileofscore

    ### Regrid
    sim_ref = sim_ref.regrid( obs_ref, iris.analysis.Linear() )
    sim_fut = sim_fut.regrid( obs_ref, iris.analysis.Linear() )

    change_factor = np.zeros(obs_ref.data.shape)

    ### Identify time axis (usually first dim)
    time_coord = sim_fut.coord(axis='t').name()
    coords = [coord.name() for coord in sim_fut.dim_coords]
    time_axis = coords.index(time_coord)

    ### Loop over non-time indices (usually lat and lon)
    collapsed_cube = sim_fut.collapsed(time_coord, iris.analysis.MEAN)

    for xy_ind in np.ndindex(collapsed_cube.shape):
        t_slice = (xy_ind[:time_axis] + (slice(None),) + xy_ind[time_axis:]) # e.g., (slice(None, None, None), 1, 1)

        ### Change Factor by Quantile Mapping
        for i, val in enumerate(obs_ref.data[t_slice]):
            percentile = percentileofscore(obs_ref.data[t_slice], val)
            cf = np.percentile(sim_fut.data[t_slice], percentile) - np.percentile(sim_ref.data[t_slice], percentile)
            tyx_ind = (xy_ind[:time_axis] + (i,) + xy_ind[time_axis:]) # e.g., (2699, 1, 1)
            change_factor[tyx_ind] = val + cf

    change_factor = _create_cube(change_factor, obs_ref, 
                            add_attr={'Calibration':'Change Factor by Quantile Mapping'})

    return change_factor


