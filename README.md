# baspy

baspy is a python package, and a set of wrappers around Iris (http://scitools.org.uk/iris/).

### Setup and import package

Setup your PYTHONPATH to point to your directory of python scripts.  Then download (or git clone) baspy python package.

```
$> mkdir ~/PYTHON
$> export PYTHONPATH="$HOME/PYTHON"  # <-- add to ~/.bashrc etc
$> cd $PYTHONPATH
$> git clone https://github.com/jshosking/baspy.git
$> ipython
>>> import baspy as bp
```

### Install Python, Iris using conda

see: http://scitools.org.uk/iris/docs/latest/installing.html

Once you have installed miniconda you can then use these commands to install iris and ipython

```
$> conda install -c scitools iris ipython
```
