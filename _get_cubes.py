import re

def get_cubes(filt_cat, constraints=None, verbose=True):

	df0       = filt_cat.iloc[0]
	path0     = df0['Path']
	split_str = re.split('/', path0)

	if ('cmip5' in split_str):
		import baspy.cmip5
		cubes = baspy.cmip5.get_cubes(filt_cat, constraints=constraints, verbose=verbose)

	if ('happi' in split_str):
		import baspy.happi
		cubes = baspy.happi.get_cubes(filt_cat, constraints=constraints, verbose=verbose)

	return cubes


def get_cube(filt_cat, constraints=None, verbose=True):

	if (len(filt_cat.index) == 1): 
		cube = get_cubes(filt_cat, constraints=constraints, verbose=verbose)
		cube = cube[0]

	if (len(filt_cat) > 1): 
		raise ValueError("Error: more than one cube present.  Try 'get_cubes' instead")
	if (len(filt_cat) == 0): 
		raise ValueError("Error: no cubes specified in catalogue.")

	return cube
