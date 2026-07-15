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

## Quick start

```python
import numpy as np
import cafpybara.analyses.hnlpi0 as ana   # or .nuecc, see "Picking an analysis"

df, pot, ngen = ana.load_mc(
    "mcbnb_cv.df",
    cuts=ana.PI0_CUT_LISTS["1shw"],
    preprocess_fn=ana.preprocess_mcbnb,
)
ana.plot_var(df, ("slc", "barycenterFM", "flashTime_calib_mod"), bins=np.linspace(0, 19, 20))
```

`load_mc` reads the dataframe, applies cuts, and runs this sample's
preprocessing; `plot_var` makes a stacked histogram using this analysis's own
categories. Every real workflow is a longer version of this same shape —
see the worked examples below for data overlays and systematics.

## Picking an analysis

**Which subpackage you import** decides the topology, not a runtime flag:

```python
import cafpybara.analyses.nuecc as ana
# or
import cafpybara.analyses.hnlpi0 as ana
```

Everything downstream (`ana.load_mc`, `ana.plot_var`, `ana.get_total_cov`,
...) then carries that topology's real defaults — nueCC's `load_mc`
defaults to `rec_key='nuecc'`, HNL/pi0's to `rec_key='rec'`. No need to pass
topology-specific values by hand; the analysis wrapper already knows them.

## Worked examples

Two analyses currently exist: **nueCC** (electron-neutrino
cross-section) and **hnlpi0** (HNL → ν + π⁰ search). Adding a third needs no
changes to existing code — see "Adding a new analysis" below.

- [`analyses/nuecc/examples/`](analyses/nuecc/examples/) —
  `signal_plots.ipynb`, `sideband_plots.ipynb`
- [`analyses/hnlpi0/examples/`](analyses/hnlpi0/examples/) —
  `hnl_analysis_v6.ipynb`

Each is a full pipeline: load files → apply cuts → compute systematics →
make plots → (hnlpi0 only) export a PYHF input dictionary. Start from these
for real analysis work, not the quick-start snippet — they show the real
cut lists, systematics setup, and plotting config for each topology.

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

Add a new folder under `cafpybara/analyses/<name>/` with its own
`config.py`/`analysis.py`/`io.py`/`plotting.py`/`funcs.py`, using `nuecc/`
or `hnlpi0/` as a template. No shared registry or base class to edit —
`cafpybara/core/` stays untouched.

Short version: every `core.*` function needing a topology-specific value (a
cut list, a category dict, a table key, ...) takes it as a **required**
argument, no default. Your analysis writes thin wrappers supplying the real
values, so callers of `cafpybara.analyses.<name>` never need to know `core`
exists.

Read "Reference: the override contract" below before shipping a new
analysis — 10 minutes, avoids missing an override.

---

## Reference: the override contract

**Every `core.*` function taking a topology-specific value has no
default.** A new analysis supplies its own by wrapping the relevant `core`
function. Below is everything a new analysis is expected to override,
gathered from what `nuecc/` and `hnlpi0/` each actually needed — listed in
write order, each file depending only on the ones above it.

**`config.py`**
- Raw path literals only — no logic, no defaults wiring. Detvar dict/file
  paths, plus an in-time-cosmic file path if a real sample exists for this
  topology. `funcs.py` below consumes these and turns them into
  `get_total_cov`'s actual defaults.

**`analysis.py`**
- At least one real cut list (a `DEFAULT_CUTS`-style `CutSpec` list). If
  several valid modes exist with no obviously-correct choice (like HNL/pi0's
  `PI0_CUT_LISTS`), don't pick one as *the* default — require `cuts=`
  explicitly (see "Design principle" below).
- Category dicts: `signal_categories`/`background_categories_<x>` (for
  `plot_var`'s stacking) and `signal_dict` (int-coded truth categories).
- `define_signal_fn` — a `define_signal(df, prefix=...)`-style function
  stamping truth-signal categories, used as `io.py`'s `define_signal_fn`
  default.

**`selection.py`** (optional)
- `select`/`select_sideband` — only needed if this topology has one
  unambiguous default cut list for `cuts=None`. Skip the file otherwise (see
  `hnlpi0`, which just re-exports `core.selection.select`). Depends only on
  `analysis.py`'s cut list(s) — nothing below this needs to exist yet.

**`preprocess.py`**
- `preprocess_mc`/`preprocess_data` (or a topology-specific composite). If
  this topology's MC/data needs real fixes (flash PE/time calibration,
  shower energy, derived angles, etc.), build a **real** composite here —
  don't assume `core.preprocess`'s no-op base is correct just because it
  was correct for `hnlpi0`. This exact mistake shipped once for `nuecc`.

**`io.py`**
- `load_mc`/`load_data`: `rec_key` (this topology's main slc-level HDF5
  table key) plus `preprocess_fn`/`define_signal_fn` defaults — wires the
  cut list, preprocessing composite, and signal-stamping function
  (`analysis.py`/`preprocess.py`) into one loader.
- Any specialized loader (e.g. `hnlpi0.load_mchnl`) needs its own
  `preprocess_fn` default, **verified independently** — don't assume it
  matches `load_mc`'s. `hnlpi0.load_mchnl` and `hnlpi0.load_mc`
  intentionally differ (real vs. no-op), since they load different
  generator outputs.

**`plotting.py`**
- `plot_var`/`plot_mc_data`/...: `categories` (this topology's default when
  `pdg=`/`mode=` aren't set), `pdg_categories`, `mode_categories`,
  `signal_dict`, and `pdg_col` if this topology ever plots by truth PDG.

**`funcs.py`**
- `get_total_cov`: reads this analysis's `config.py` paths into the
  `detvar_dict`/`detvar_files` default, plus `intime_file`/`intime_key`/
  `offbeam_value`/`intime_preprocess_fn` **only if a real in-time-cosmic
  sample exists** — otherwise raise a clear error on `'cosmic'` rather than
  silently reaching for another topology's sample. Also supplies the
  `uncertainty_keys` default set.

**`core/detvar/process_detvars.py`**
- One new entry per dict/function — `_SLC_KEY`,
  `_default_preprocess_fn`, `_selection_fn_map` — keyed by the new
  analysis's name. The one place inside `core/` that legitimately needs an
  edit, since its CLI resolves an analysis's slc_key/preprocess_fn/selection
  functions by name.

**`__init__.py`**
- `from ...core.<module> import *` for **every** `core` submodule
  (`utils`, `io`, `plotting`, `physics`, `syst`, `selection`, `classes`,
  `funcs`, `preprocess`, `detvar`), *before* this analysis's own
  `from .<module> import *` lines, so real overrides correctly shadow the
  core generics in the flat namespace. Missing one has been the single most
  common bug in this repo — worth a quick `hasattr` sweep against `core`'s
  `__all__` lists before shipping.
- Listed last because its *real content* — re-exporting every file above —
  can't be finalized until they all exist. (An empty stub has to exist from
  the start so the folder is importable while you write the rest; that's a
  trivial, content-free step, not what this entry tracks.)

### Design principle: required > silently-wrong default

`core/` functions require an explicit argument instead of picking a
default, so a missing topology-specific value is a loud `TypeError`/
`ValueError` at the call site, not a silent wrong answer three layers down.
Apply the same principle one level down in an analysis's own wrapper
defaults: if there's no single obviously-correct default for *this*
topology (multiple valid cut-list modes, no real in-time-cosmic sample,
etc.), don't invent one — require the caller to pass it, or raise a clear
error explaining why it's unavailable (see `hnlpi0.funcs.get_total_cov`
raising on `'cosmic'`, or its `cuts` having no default at all).

## Common mistakes

### `get_total_cov`/`SystematicsInput` needs `cuts=` too, not just your dataframe

By the time `reco_df` reaches `get_total_cov`, it's already been filtered to
your analysis selection — you passed `cuts=` to `load_mc`/`load_data`
earlier. But if you ask for `'detv'` or `'cosmic'` uncertainties,
`get_total_cov` also pulls in a *separate* comparison sample (a
detector-variation sample, or an in-time-cosmic sample) — and that sample
does **not** inherit your selection automatically. You have to tell it,
via the same `cuts=`:

```python
# Wrong -- reco_df is selected, but the detvar comparison sample isn't.
# Raises a ValueError explaining exactly this, rather than running.
systs_cfg = ana.SystematicsInput(
    mcbnb_pot=mcbnb_pot,
    detvar_dict=detvar_dict,
)

# Right -- cuts= matches whatever you loaded reco_df with.
systs_cfg = ana.SystematicsInput(
    mcbnb_pot=mcbnb_pot,
    detvar_dict=detvar_dict,
    cuts=ana.DEFAULT_CUTS,   # whatever cut list you passed to load_mc/load_data
)
```

Forgetting this used to fail *silently* — the comparison would quietly run
on the full, unselected population instead of your actual selection,
inflating the `'detv'` (or `'cosmic'`) uncertainty for no physical reason.
It now raises a clear `ValueError` instead, so you find out immediately
rather than after staring at a suspiciously large error bar. Same fix
applies to `'cosmic'`, via `cuts=`/`intime_cuts=`.
