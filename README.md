# baspy

baspy is a python package, and a set of wrappers around Iris (http://scitools.org.uk/iris/) and (over time) also Xarray.

### 1. Install Python, Iris using conda

see: http://scitools.org.uk/iris/docs/latest/installing.html

Once you have installed miniconda you can then use these commands to install iris and ipython

```
$> conda install -c conda_forge iris ipython
```

### 2. Setup and import package

Setup your PYTHONPATH to point to your directory of python scripts.  Then download (or git clone) baspy python package.

```
$> mkdir ~/PYTHON
$> export PYTHONPATH="$HOME/PYTHON"  # <-- add to ~/.bashrc etc
$> cd $PYTHONPATH
$> git clone https://github.com/scott-hosking/baspy.git
$> ipython
>>> import baspy as bp
```

### 3. Define the directory and filename structures of your local datasets

see and edit datasets.py

### 4. Usage

To read in a small number of cubes:

```
import baspy as bp
cat = bp.catalogue(dataset='cmip5', Model='HadGEM2-CC', RunID='r1i1p1', 
					Experiment='historical', Var=['tas', 'pr'], Frequency='mon')
cubes = bp.get_cubes(cat)
```

To loop over many models, reading one model at a time:

```
import baspy as bp
import numpy as np

cat = bp.catalogue(dataset='cmip5', Experiment='amip', Var='tas', Frequency='mon')

uniq_models = np.unqiue(cat['Model'])

for model in uniq_models:
	filtered_cat = cat[ cat['Model'] == model ]
	cubes = bp.get_cubes(filtered_cat)
```
