import glob
import re
import os
import pandas as pd

happi_cat_fname = 'happi_catalogue.csv'
happi_dir       = '/group_workspaces/jasmin/bas_climate/data/happi/data/'

### Location of personal catologue file
__baspy_path = os.path.expanduser("~/.baspy")
if not os.path.exists(__baspy_path): 
	os.makedirs(os.path.expanduser(__baspy_path))
cat_file = __baspy_path+'/'+happi_cat_fname

### If personal catologue file does not exist then copy shared catologue file
__shared_cat_file = '/group_workspaces/jasmin/bas_climate/data/data_catalogues/'+happi_cat_fname
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