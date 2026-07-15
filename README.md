# cafpybara

A general CAF-analysis toolkit for SBND (CAF + Python + capybara), built for
notebook and script workflows where CAF-derived dataframes have already been
produced (typically via [`cafpyana`](https://github.com/sungbinoh/cafpyana))
and you want to run selection, plotting, and uncertainty studies.

## Layout

Mirrors cafpyana's own `analysis_village/` convention: a shared `core/` with
zero topology defaults, and one self-contained folder per analysis under
`analyses/`.

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

## Usage

Pick an analysis by importing its subpackage -- topology choice is made by
*which module you import*, not by a runtime parameter:

```python
import cafpybara.analyses.nuecc as ana
# or
import cafpybara.analyses.hnlpi0 as ana

df, pot, ngen = ana.load_mc("mc.df", cuts=ana.DEFAULT_CUTS)
ana.plot_var(df, var, bins)
```

Each village's own `io.py`/`plotting.py`/`funcs.py`/`selection.py` are thin
wrappers pre-filling `cafpybara.core`'s generic functions with that
topology's real defaults (e.g. nueCC's `load_mc` defaults `rec_key='nuecc'`;
HNL/pi0's defaults `rec_key='rec'`).

## Adding a new analysis

Add a new folder under `cafpybara/analyses/<name>/` with its own
`config.py`/`analysis.py`/`io.py`/`plotting.py`/`funcs.py` following the
existing two villages (`nuecc/`, `hnlpi0/`) as a template. No shared registry
or base class to edit -- `cafpybara/core/` never needs to change.

**Every `core.*` function that takes a topology-specific value has no
default for it.** A new village's job is to supply real defaults for its own
topology by wrapping the relevant `core` function. The table below lists
every place a new village is expected to override something, gathered from
what `nuecc/` and `hnlpi0/` each actually had to supply.

| File | Function / value | Must supply |
|---|---|---|
| `config.py` | -- | Detvar dict/file paths, in-time-cosmic file path (only if a real in-time-cosmic sample exists for this topology -- otherwise omit and have `funcs.get_total_cov` raise if `'cosmic'` is requested, see `hnlpi0/funcs.py`) |
| `analysis.py` | cut list(s) | At least one real `CutSpec` list (e.g. `DEFAULT_CUTS`). If there's more than one valid mode with no single obviously-correct choice (like HNL/pi0's `PI0_CUT_LISTS`), don't pick one as *the* default -- make callers pass `cuts=` explicitly instead (see "Design principle" below) |
| `analysis.py` | category dict(s) | `signal_categories`/`background_categories_<x>` (for `plot_var`'s stacking) and `signal_dict` (int-coded truth categories) |
| `analysis.py` | `define_signal_fn` | A `define_signal(df, prefix=...)`-style function stamping truth-signal categories, used as `io.py`'s `define_signal_fn` default |
| `preprocess.py` | `preprocess_mc`/`preprocess_data` (or a topology-specific composite) | If this topology's MC/data actually needs real fixes (flash PE/time calibration, shower energy, derived angles, etc.), build a **real** composite here -- do **not** assume `core.preprocess`'s no-op base is correct for a new topology just because it was correct for `hnlpi0`. This exact mistake shipped once for `nuecc` (see "A real bug this pattern already caught" below) |
| `io.py` | `load_mc`/`load_data` | `rec_key` (the HDF5 table key for this topology's main slc-level table) and `preprocess_fn`/`define_signal_fn` defaults, pre-filling `core.io.load_mc`/`load_data` |
| `io.py` | any specialized loader (e.g. `hnlpi0.load_mchnl`) | Its own `preprocess_fn` default -- **verify independently**, don't assume it matches `load_mc`'s default. `hnlpi0.load_mchnl` and `hnlpi0.load_mc` intentionally have *different* correct defaults (real vs. no-op) because they load different generator outputs |
| `selection.py` (optional) | `select`/`select_sideband` | Only needed if this topology has one unambiguous default cut list to fall back to when `cuts=None`. Skip this file entirely if not (see `hnlpi0`, which just re-exports `core.selection.select` directly) |
| `plotting.py` | `plot_var`/`plot_mc_data`/... | `categories` (falls back to this topology's own category dict when `pdg=`/`mode=` aren't set), `pdg_categories`, `mode_categories`, `signal_dict`, and (if this topology ever plots by truth PDG) `pdg_col` |
| `funcs.py` | `get_total_cov` | `detvar_dict`/`detvar_files` default resolution, `uncertainty_keys` default set, and `intime_file`/`intime_key`/`offbeam_value`/`intime_preprocess_fn` **only if a real in-time-cosmic sample exists** -- otherwise raise a clear error when `'cosmic'` is requested rather than silently reaching for another topology's sample |
| `core/detvar/process_detvars.py` | `_VILLAGE_SLC_KEY`, `_default_preprocess_fn`, `_selection_fn_map` | One new entry per dict/function, keyed by the new village's name -- this is the one place inside `core/` that legitimately needs a small edit, since `process_detvars.py`'s CLI has to resolve a village's slc_key/preprocess_fn/selection functions by name |
| `__init__.py` | -- | `from ...core.<module> import *` for **every** `core` submodule (`utils`, `io`, `plotting`, `physics`, `syst`, `selection`, `classes`, `funcs`, `preprocess`, `detvar`) *before* this village's own `from .<module> import *` lines, so the village's real overrides correctly shadow the core generics in the flat namespace. Missing one of these has been the single most common bug in this repo so far (see below) |

### Design principle: required > silently-wrong default

`core/` functions raise or require an explicit argument rather than picking
a default, specifically so that forgetting to supply a topology-specific
value is a loud `TypeError`/`ValueError` at the call site, not a silent
wrong answer three layers down. When writing a village's own wrapper
defaults, apply the same principle one level down: if there's no single
obviously-correct default for *this* topology (multiple valid cut-list
modes, no real in-time-cosmic sample, etc.), don't invent one -- require the
caller to pass it, or raise a clear error explaining why it's unavailable
(see `hnlpi0.funcs.get_total_cov` raising on `'cosmic'`, or `hnlpi0.funcs.
get_total_cov`'s `cuts` having no default at all).

### A real bug this pattern already caught

Two real bugs shipped from getting the above table wrong, both found live
(not by static checking) and both the same underlying mistake -- a village
wrapper defaulted to `core`'s generic/no-op version of something instead of
building and using its own real one:

1. `nuecc.load_mc`/`load_data` defaulted `preprocess_fn` to `core.preprocess
   .preprocess_mc`/`preprocess_data` (the topology-agnostic no-op, correct
   for `hnlpi0` but not for `nuecc`) instead of a real nueCC composite
   (flash PE/time calibration, shower energy, derived phi). No such
   composite existed at all at first -- it was wrongly assumed nueCC's own
   preprocessing was a no-op too, based on reading the wrong reference
   branch. Silently dropped a data selection from 39 events to 4 on an
   otherwise byte-identical cut chain, and affected every MC dataframe the
   same way.
2. `hnlpi0.load_mchnl` defaulted `preprocess_fn` to the no-op `preprocess_mc`
   instead of its own real `preprocess_mchnl` (MeVPrtl-generator timing
   calibration) -- found during the audit that caught bug 1, by diffing
   every wrapper default against the reference implementation rather than
   assuming a fix in one place meant the pattern was fixed everywhere.

**Takeaway for review**: when adding or auditing a village, check every
default in its wrapper functions against that topology's actual reference
behavior (a prior notebook, an ancestor repo, whatever the topology's
existing ground truth is) -- never assume a default is a no-op/safe just
because it happens to be correct for another village, and never assume
fixing one wrapper function fixed the pattern everywhere else it appears.
