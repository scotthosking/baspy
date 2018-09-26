# BASpy

baspy is a python package to make it easier to analyse large climate 
datasets using Xarray (http://xarray.pydata.org) and Iris (http://scitools.org.uk/iris/).

### 1. Setup and import package

Setup your PYTHONPATH to point to your directory of python scripts.  Then 
download (or git clone) baspy python package.

```
    $> mkdir ~/PYTHON
    $> export PYTHONPATH="$HOME/PYTHON"  # <-- add to ~/.bashrc etc
    $> cd $PYTHONPATH
    $> git clone https://github.com/scott-hosking/baspy.git
    $> ipython
    >>> import baspy as bp
```

### 2. Define the directory and filename structures of your local datasets

see and edit datasets.py

Once you have setup this all the loading of files should become transparent

### 3. Usage

Example:

```
    import baspy as bp

    ### Retrieve a filtered version of the CMIP5 catalogue as a Pandas DataFrame
    df = bp.catalogue(dataset='cmip5', Model='HadGEM2-CC', RunID='r1i1p1', 
    					Experiment='historical', Var=['tas', 'pr'], Frequency='mon')

    ### Iterate over rows in catalogue
    for index, row in df.iterrows():

        ### In Xarray
        ds = xr.open_mfdataset(bp.get_files(row))

        ### In iris
        cubes = bp.get_cubes(row)
```
