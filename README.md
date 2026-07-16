# cafpybara

A general CAF-analysis toolkit for SBND.

The plotting/selection/systematics layer that sits *after* `cafpyana` turns
CAF ntuples into flat HDF5 dataframes.

## Setup

1. Get a `cafpyana` clone with dataframes already produced (see its own
   README). `cafpybara` reads dataframes, it doesn't make them.
2. Clone this repo anywhere — it doesn't need to sit next to `cafpyana`.
3. Point `CAFPYANA_PATH` in `cafpybara/__init__.py` at your `cafpyana`
   clone:
   ```python
   CAFPYANA_PATH = "/path/to/your/cafpyana"
   ```
   The repo's one hardcoded path — `cafpybara` auto-adds it to `sys.path`,
   so imports like `from makedf.util import InFV` resolve without a manual
   `PYTHONPATH`.
4. Install dependencies from `pip_requirements.txt` (numpy, pandas,
   matplotlib, scikit-learn, xgboost, pyhf, etc — versions confirmed
   working on EAF's `venv_eaf` kernel as of 2026-07-14).
5. Make the directory *containing* `cafpybara/` importable — run notebooks
   from there, or add it to `sys.path`:
   ```python
   import sys
   sys.path.insert(0, "/path/to/parent/of/cafpybara")
   import cafpybara.analyses.hnlpi0 as ana
   ```
   On a shared environment (e.g. EAF), a confusing `KeyError` or
   stale-looking behavior right after pulling new code usually means
   another install is shadowing your clone on `sys.path` — check with
   `pip show -f cafpybara`/`cafpyana` and `pip uninstall` the stale one.

## Picking an analysis

Which subpackage you import decides the topology, not a runtime flag —
everything downstream (`ana.load_mc`, `ana.plot_var`, `ana.get_total_cov`)
then carries that topology's real defaults. Two exist today; adding a
third needs no changes to existing code (see "Adding a new analysis"):

- **nueCC** (electron-neutrino cross-section) —
  `import cafpybara.analyses.nuecc as ana` —
  [`analyses/nuecc/examples/`](analyses/nuecc/examples/): `signal_plots.ipynb`,
  `sideband_plots.ipynb`
- **hnlpi0** (HNL → ν + π⁰ search) —
  `import cafpybara.analyses.hnlpi0 as ana` —
  [`analyses/hnlpi0/examples/`](analyses/hnlpi0/examples/): `hnl_analysis_v6.ipynb`
  (the real pipeline), `selection_walkthrough.ipynb` (start here if `cuts=`
  is new to you)

Each example notebook is a full pipeline: load files → apply cuts →
compute systematics → make plots → (hnlpi0 only) export a PYHF input
dictionary.

## Layout

```
cafpybara/
  core/               # topology-agnostic mechanics: selection, io, plotting,
                       # systematics machinery, detvar store. Every
                       # topology-specific value (rec_key, cut list, category
                       # dict, detvar/intime paths) is a required parameter
                       # here -- no silent default favors one topology.
  analyses/
    nuecc/              # nueCC cross-section analysis
      examples/           # signal_plots.ipynb, sideband_plots.ipynb
    hnlpi0/             # HNL/pi0 (nu_pi0) analysis
      examples/           # hnl_analysis_v6.ipynb
```

`core/` never contains topology-specific behavior. Reaching for an `if
topology == ...` branch inside `core/`? That logic belongs in an analysis's
own wrapper instead — see below.

## Adding a new analysis

Start from [`analyses/_template/`](analyses/_template/) — a static,
non-functional scaffold with the required files
(`config.py`/`analysis.py`/`preprocess.py`/`io.py`/`funcs.py`/
`plotting.py`), every topology-specific value replaced with an
obviously-broken placeholder rather than a real value copied from another
analysis. Copy it to `cafpybara/analyses/<name>/` and fill in the `# TODO`s.

[`analyses/_template/examples/build_a_new_analysis.ipynb`](analyses/_template/examples/build_a_new_analysis.ipynb)
walks through each file in write order, citing the real bug that shaped it.
No real Fermilab/EAF data needed to run it.

Before shipping it, run `python scripts/verify_new_analysis.py <name>` — a
structural conformance check (no real data needed) covering re-export
completeness, `get_total_cov` identity, no-op-preprocessing defaults, and
dead kwargs in your example notebooks' `systs_input`/`SystematicsInput`/
`PlottingConfig` calls.

No shared registry or base class to edit — `cafpybara/core/` stays
untouched. See "Reference: the override contract" below for the per-file
checklist.

---

## Reference: the override contract

**Every `core.*` function taking a topology-specific value has no
default** — a new analysis supplies its own by wrapping the relevant
`core` function. Write order, each file depending only on the ones above:

- **`config.py`** — path literals only (detvar files, in-time-cosmic file
  if it exists).
- **`analysis.py`** — a real cut list (`DEFAULT_CUTS`), category dicts
  (`signal_categories`, `signal_dict`), `define_signal_fn`. If several cut
  modes exist with no obvious default, require `cuts=` explicitly instead
  of picking one.
- **`selection.py`** (optional) — `select`/`select_sideband`, only if
  there's one unambiguous default cut list. Skip it otherwise.
- **`preprocess.py`** — a real `preprocess_mc`/`preprocess_data`
  composite if this topology needs real fixes; the generic no-op is only
  correct if it genuinely needs none.
- **`io.py`** — `load_mc`/`load_data` with this topology's `rec_key` and
  `preprocess_fn`/`define_signal_fn` defaults. Any specialized loader
  needs its own `preprocess_fn` default, verified independently.
- **`plotting.py`** — `categories`, `pdg_categories`, `mode_categories`,
  `signal_dict`, `pdg_col` if used.
- **`funcs.py`** — `systs_input()`, resolving `config.py`'s paths into
  `detvar_dict`/`detvar_files` and `uncertainty_keys`; raise on `'cosmic'`
  if no real in-time-cosmic sample exists. No `get_total_cov` override —
  `core.funcs.get_total_cov` is the only one.
- **`core/detvar/process_detvars.py`** — a new dict key or `elif` branch
  in each of `_SLC_KEY`, `_default_preprocess_fn`, `_selection_fn_map`,
  keyed/matched by the new analysis's name. The one place in `core/` that
  legitimately needs an edit.
- **`__init__.py`** — `from ...core.<module> import *` for every `core`
  submodule, *before* this analysis's own `from .<module> import *` lines.
  Listed last since it re-exports everything above.

**Design principle**: required argument, not a default — a missing value
should be a loud error at the call site, not a silent wrong answer further
down. Apply this in your own wrapper defaults too: no single obviously
-correct default means require the caller to pass it, or raise explaining
why.

## Common mistakes

### `get_total_cov`/`SystematicsInput` needs `cuts=` too, not just your dataframe

`get_total_cov`'s `'detv'`/`'cosmic'` uncertainties pull in a separate
comparison sample (detector-variation or in-time-cosmic) that does **not**
inherit `reco_df`'s selection automatically — pass the same `cuts=` you
used for `load_mc`/`load_data`:

```python
systs_cfg = ana.systs_input(
    mcbnb_pot,
    detvar_dict=detvar_dict,
    cuts=ana.DEFAULT_CUTS,   # must match what you loaded reco_df with
)
```

Omitting `cuts=` when `'detv'`/`'cosmic'` are requested raises a
`ValueError` rather than silently comparing against the wrong population.
