# BASpy

BASpy is a Python package for working with large climate model datasets. It provides a catalogue system for indexing and filtering datasets (CMIP5, CMIP6) and uses [Xarray](https://docs.xarray.dev/en/stable/) to load the data.

---

## Requirements

- Python 3.7+
- [Xarray](https://docs.xarray.dev/en/stable/)
- [pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [pyarrow](https://arrow.apache.org/docs/python/)

---

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/scotthosking/baspy.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/scotthosking/baspy.git
cd baspy
pip install -e .
```

> **Note:** If you previously installed BASpy by adding its directory to `PYTHONPATH`, remove that entry from your shell config — it is no longer needed and will conflict with the pip-installed package.

---

## Catalogue files

BASpy uses pre-built catalogue files (Parquet format) stored in `~/.baspy/`. These index the files available on your system for each dataset.

Catalogue files can be downloaded from:

```
http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/
```

For example, to download the CMIP5 catalogue:

```bash
wget http://gws-access.ceda.ac.uk/public/bas_climate/files/baspy/cmip5_catalogue.csv -O ~/.baspy/cmip5_catalogue.csv
```

Existing CSV catalogues are automatically converted to Parquet on first use.

To rebuild a catalogue from scratch (e.g. after new data has been added to the archive):

```python
bp.catalogue(dataset='cmip5', refresh=True)
```

---

## Usage

### Filter the catalogue

```python
import baspy as bp

df = bp.catalogue(dataset='cmip5',
                  Model='HadGEM2-CC',
                  RunID='r1i1p1',
                  Experiment='historical',
                  Var=['tas', 'pr'],
                  Frequency='mon')

print(df.head())
```

### Load data with Xarray

```python
for index, row in df.iterrows():
    ds = bp.open_dataset(row)
    print(ds)
```

### Read everything (bypass default filters)

```python
df = bp.catalogue(dataset='cmip6', read_everything=True)
```

---

## Adding or editing datasets

Dataset configurations (root paths, directory structures, filename structures) are defined in [`datasets.json`](datasets.json). To add support for a new dataset, add an entry following the same structure as the existing ones.

---

## Credits

Created by Scott Hosking. Contributors: Tom Bracegirdle, Tony Phillips.
