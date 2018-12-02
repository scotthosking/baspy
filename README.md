# BASpy

baspy is a python package to make it easier to analyse large climate datasets
using Xarray (http://xarray.pydata.org), Iris (http://scitools.org.uk/iris/), 
or any other python package that can read in netcdf/PP/grib/HDF files.

### 1. Setup package

Setup your PYTHONPATH to point to your directory of python scripts.  Then 
download (or git clone) baspy python package.

```
    $> mkdir ~/PYTHON
    $> export PYTHONPATH="$HOME/PYTHON"  # <- add to ~/.bashrc
    $> cd $PYTHONPATH
    $> git clone https://github.com/scott-hosking/baspy.git
```

### 2. Define the directory and filename structures of your local datasets

see and edit datasets.py

Once you have set this up all file loading should become transparent

### 3. Usage

Reading data:

```
    import baspy as bp
    import xarray as xr

    ### Retrieve a filtered version of the CMIP5 catalogue as a Pandas DataFrame
    df = bp.catalogue(dataset='cmip5', Model='HadGEM2-CC', RunID='r1i1p1', 
                        Experiment='historical', Var=['tas', 'pr'], 
                        Frequency='mon')

    ### Iterate over rows in catalogue
    for index, row in df.iterrows():

        ### In Xarray
        ds = xr.open_mfdataset(bp.get_files(row))

        ### Or... In Iris
        cubes = bp.get_cube(row)
```

Other Examples: 
* [Xarray with BASpy (Notebook)](https://github.com/scott-hosking/baspy/blob/master/examples/xarray_examples.ipynb)
* [Statistical Downscaling in Iris (Script)](https://github.com/scott-hosking/baspy/blob/master/examples/statistical_downscaling.py)
