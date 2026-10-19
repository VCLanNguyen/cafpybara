# cafpybara

A general CAF-analysis toolkit for SBND.

## What it does

The plotting/selection/systematics layer over the HDF5 dataframes
`cafpyana` produces from CAF ntuples.

## Structure

```
cafpybara/
  core/               # topology-agnostic mechanics -- selection, io, plotting,
                       # systematics, detvar store
    detvar/             # detvar store: process_detvars.py, recomb.py
    exclusive/          # exclusive/nominal-sample overlap removal
  analyses/
    nuecc/              # nueCC cross-section analysis
      examples/           # signal_plots.ipynb, sideband_plots.ipynb
      exclusive/          # merge_ar23.py -- merge exclusive-sample weights
    hnlpi0/             # HNL/pi0 (nu_pi0) analysis
      examples/           # hnl_plotting.ipynb, verify_1shw_drift_check.ipynb
    _template/          # scaffold for a new analysis
      instructions/       # step1-4 onboarding notebooks
  scripts/            # verify_new_analysis.py (conformance check),
                      # verify_detvar_drift_check.py, strip_notebook_outputs.py
```

## Getting started

### Setup

1. Get a `cafpyana` clone with dataframes already produced (see its own
   README). `cafpybara` reads dataframes, it doesn't make them.
2. Clone this repo anywhere — it doesn't need to sit next to `cafpyana`.
3. Set the `CAFPYANA_PATH` environment variable to your `cafpyana` clone
   (required -- `import cafpybara` raises without it):
   ```bash
   export CAFPYANA_PATH=/path/to/your/cafpyana   # e.g. in ~/.bashrc
   ```
   or, in a notebook, before importing `cafpybara`:
   ```python
   os.environ["CAFPYANA_PATH"] = "/path/to/your/cafpyana"
   ```
4. Install dependencies from `pip_requirements.txt` (numpy, pandas,
   matplotlib, scikit-learn, xgboost, pyhf, etc).
5. Make the directory *containing* `cafpybara/` importable — run notebooks
   from there, or add it to `sys.path`:
   ```python
   import sys
   sys.path.insert(0, "/path/to/parent/of/cafpybara")
   import cafpybara.analyses.hnlpi0 as ana
   ```

### Use an existing analysis

- **nueCC** (electron-neutrino cross-section) —
  `import cafpybara.analyses.nuecc as ana` —
  [`analyses/nuecc/examples/`](analyses/nuecc/examples/): `signal_plots.ipynb`,
  `sideband_plots.ipynb`
- **hnlpi0** (HNL → ν + π⁰ search) —
  `import cafpybara.analyses.hnlpi0 as ana` —
  [`analyses/hnlpi0/examples/`](analyses/hnlpi0/examples/): `hnl_plotting.ipynb`

Each example notebook is a full pipeline: load files → apply cuts →
compute systematics → make plots.

### Add a new analysis

* Copy [`analyses/_template/`](analyses/_template/) to
  `cafpybara/analyses/<name>/` — a static, non-functional scaffold
  (`config.py`/`analysis.py`/`preprocess.py`/`io.py`/`funcs.py`/
  `plotting.py`), every topology-specific value an obviously-broken
  placeholder.
* Follow [`analyses/_template/instructions/`](analyses/_template/instructions/)
* Before shipping it: run `python scripts/verify_new_analysis.py <name>`
  — a structural conformance check, no real data needed.
* No shared registry or base class to edit — `cafpybara/core/` stays
  untouched.
