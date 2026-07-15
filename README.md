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
existing two villages as a template. No shared registry or base class to
edit -- `cafpybara/core/` never needs to change.
