import glob
import re
import os
import pandas as pd
import iris
import iris.coords as coords
import baspy.util


cat_fname = 'happi_catalogue.csv'
happi_dir = '/group_workspaces/jasmin/bas_climate/data/happi/data/'

### Location of personal catologue file
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))
cat_file = __baspy_path+'/'+cat_fname

### If personal catologue file does not exist then copy shared catologue file
__shared_cat_file = '/group_workspaces/jasmin/bas_climate/data/data_catalogues/'+cat_fname
if (os.path.isfile(cat_file) == False):	
	print("Catalogue of HAPPI data does not exist, this may be the first time you've run this code")
	print('Copying shared catalogue to '+__baspy_path)
	import shutil
	shutil.copy2(__shared_cat_file, cat_file)

def __refresh_shared_catalogue():
	'''
	Rebuild the HAPPI catalogue
	'''

	print("Building catalogue now...")

	### Get paths for all HAPPI data
	dirs = glob.glob(happi_dir+'/*/*/*/*/*/*/*/*/*')
	dirs = filter(lambda f: os.path.isdir(f), dirs)

	### write data to catalogue (.csv) using a Pandas DataFrame
	rows = []
	for dir in dirs:

	    parts = re.split('/', dir)[7:]
	    # parts.pop(7)

	    a = re.split('/', dir)
	    dir = '/'.join(a)

	    parts.append(dir)        
	    rows.append(parts)

	df = pd.DataFrame(rows, columns=['Centre','Model','Experiment','CMOR','Version','Frequency','SubModel','Var','RunID','Path'])

	### save to local dir
	df.to_csv(__shared_cat_file, index=False)




def callback(cube, field, filename):
	"""
	A function which adds a "RunID" coordinate to the cube
	"""

	filename = re.split('/',filename)[-1]

	### Extract the Model name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[2]
	new_coord = coords.AuxCoord(label, long_name='Model', units='no_unit')
	cube.add_aux_coord(new_coord)

	### Extract the Experiment name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[3]
	new_coord = coords.AuxCoord(label, long_name='Experiment', units='no_unit')
	cube.add_aux_coord(new_coord)

	### Extract the RunID name from the filename
	split_str = re.split('_',filename) # split string by delimiter
	label = split_str[6]
	new_coord = coords.AuxCoord(label, long_name='RunID', units='no_unit')
	cube.add_aux_coord(new_coord)

	### Add additional time coordinate categorisations
	if (len(cube.coords(axis='t')) > 0):

		time_name = cube.coord(axis='t').var_name

		iris.coord_categorisation.add_year(cube, time_name, name='year')
		iris.coord_categorisation.add_month_number(cube, time_name, name='month')

		### Add season
		seasons = ['djf', 'mam', 'jja', 'son']
		iris.coord_categorisation.add_season(cube, time_name,      name='clim_season', seasons=seasons)
		iris.coord_categorisation.add_season_year(cube, time_name, name='season_year', seasons=seasons)




def get_cubes(filt_cat, constraints=None, verbose=True):
	"""
	Use filtered catalogue to read files and return a CubeList

	>>> cat      = bp.happi.catalogue(Experiment='historical', Frequency='mon', Var='psl')
	>>> cubelist = bp.happi.get_cubes(cat)
	"""

	### start with empty cubelist, then expand within loop
	cubelist2 = iris.cube.CubeList([])

	count = 0
	len_filt = len(filt_cat.index)

	for i in filt_cat.index:
		filt   = filt_cat[filt_cat.index == i]
		path   = filt['Path'].values[0]
		model  = filt['Model'].values[0]
		run_id = filt['RunID'].values[0]
		var    = filt['Var'].values[0]
		exp    = filt['Experiment'].values[0]
		
		### Print progress to screen
		if (verbose == True): 
			count = count+1
			print('['+str(count)+'/'+str(len_filt)+'] HAPPI '+model+' '+run_id+' '+exp+' '+var)

		netcdfs = os.listdir(path)
		
		### Remove hidden files that start with '.'
		nc2 = []
		for nc in netcdfs:
			if (nc.startswith('.') == False): nc2.append(nc)
		netcdfs = nc2

		### Remove files from chararray where run id not in 
		### netcdf filenames or remove files that end with '.nc4' 
		### (Note: EC-Earth has '*.nc4' files present)
		del_netcdfs = []	
		for nc in netcdfs:
			
			if (run_id not in nc):
					print('>> WARNING: Detected misplaced files'
					' in '+path+' <<')
					print(run_id, nc)
				
		### Remove netcdfs according to del_netcdfs
		for k in del_netcdfs: 
			if (k in netcdfs): netcdfs.remove(k)

		### Read data with callback to add Experiment (Run) ID to 
		### distinguish between ensemble memebers
		cubelist1 = iris.cube.CubeList([])
		for j in netcdfs:
			dirfilename = path+'/'+j
			### contraint by var_name
			con  = iris.Constraint(
				cube_func=lambda cube: cube.var_name == var)
			
			### Additional constrains (level, time)
			if (constraints != None): con = con & constraints
			
			cube = iris.load(dirfilename, callback=callback, constraints=con)

			if (len(cube) > 1): raise ValueError('more than one cube loaded, expected only one!')

			if ( (type(cube) == iris.cube.CubeList) & (len(cube) == 1) ):	
				cube = cube[0]
			
				### Remove attributes to enable cubes to concatenate
				cube.attributes.clear()
				
				### Create cubelist from cubes
				cubelist1.extend([cube])



		### Change reference time of cubes so times match in order to 
		### encourage cubes to concatenate
		iris.util.unify_time_units(cubelist1)
		
		### Remove temporal overlaps
		cubelist1 = baspy.util.rm_time_overlaps(cubelist1)

		### Unify lat-lon grid
		#cubelist1 = baspy.util.util.unify_grid_coords(cubelist1, cubelist1[0])
		
		### if the number of netcdf files (and cubes) >1 then 
		### merge them together
		cube = iris.cube.CubeList.concatenate_cube(cubelist1)
		
		#### Create a cubelist from cubes
		cubelist2.extend([cube])

	return cubelist2
