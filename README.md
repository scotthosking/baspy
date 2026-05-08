# BASpy
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

BASpy is a Python package for working with large climate model datasets. It provides a catalogue system for indexing and filtering datasets (CMIP5, CMIP6).

---

## Requirements

- Python 3.7+
- [pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [pyarrow](https://arrow.apache.org/docs/python/)
- [Xarray](https://docs.xarray.dev/en/stable/)

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

---

## Machine configuration

BASpy uses a config file at `~/.baspy/config.json` to know which machine you are on, and therefore which dataset paths and catalogue files to use.

Set your machine on first use:

```python
import baspy as bp
bp.set_config('jasmin')
```

This writes `{"machine": "jasmin"}` to `~/.baspy/config.json`. BASpy will then load `datasets_jasmin.json` from the package for dataset root paths and directory structures.

To check your current config:

```python
bp.get_config()
```

To add support for a new machine, create a `datasets_{machine}.json` file in the `baspy/` package directory following the same structure as `datasets_jasmin.json`.

---

## Catalogue files

BASpy uses pre-built catalogue files (Parquet format) stored in `~/.baspy/`. These index the files available on your system for each dataset.

Bundled catalogue files are included in the package under `baspy/catalogues/` and are copied to `~/.baspy/` automatically on first use. Currently bundled:

| Dataset | Coverage |
|---------|----------|
| `cmip6` | CMIP and ScenarioMIP activities |

To rebuild a catalogue from scratch (e.g. after new data has been added to the archive):

```python
bp.catalogue(dataset='cmip6', refresh=True)
```

Existing CSV catalogues are automatically migrated to Parquet on first use.

---

## Usage

### Filter the CMIP5 catalogue

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

### Filter the CMIP6 catalogue

Note: CMIP6 does not have a `Frequency` column — use `CMOR` instead (e.g. `Amon` for monthly atmosphere).

```python
df = bp.catalogue(dataset='cmip6',
                  Experiment='historical',
                  Var=['tas', 'pr'],
                  CMOR='Amon')
```

### Read everything (bypass default filters)

```python
df = bp.catalogue(dataset='cmip6', read_everything=True)
```

---

## Adding or editing datasets

Dataset configurations (root paths, directory structures, filename structures) are defined in `datasets_{machine}.json`. To add support for a new dataset on an existing machine, add an entry to the relevant JSON file following the same structure as the existing ones.

---

## Credits

Created by Scott Hosking. Contributors: [@TomBracegirdle](https://github.com/TomBracegirdle), [@TonyP-BAS](https://github.com/TonyP-BAS).

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://scotthosking.com"><img src="https://avatars.githubusercontent.com/u/10783052?v=4?s=100" width="100px;" alt="Scott Hosking"/><br /><sub><b>Scott Hosking</b></sub></a><br /><a href="https://github.com/scotthosking/baspy/commits?author=scotthosking" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!