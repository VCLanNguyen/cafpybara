"""Generic cut infrastructure, shared by every analysis topology.

:class:`~cafpybara.core.classes.CutSpec` (defined in
:mod:`cafpybara.core.classes`) and the functions to build, modify, and apply
cut sequences live here. Analysis-specific cut sequences (e.g. nueCC's
``DEFAULT_CUTS``/``SIDEBAND_CUTS``, HNL/pi0's ``PI0_CUT_LISTS``) and signal
categorisation live in each analysis's own
``cafpybara/analyses/<topology>/analysis.py``.

Unlike the original nueCC-only ``select()``, ``cuts`` here has no default --
even a single topology (HNL/pi0) has multiple valid cut-list modes, so there
is no one obviously-correct fallback. Pass ``cuts=`` explicitly, or use a
per-analysis convenience wrapper (e.g. ``nuecc.selection.select`` defaults to
``DEFAULT_CUTS``).

**Tighten or loosen a cut**::

    from cafpybara.core.selection import modify_cut, select

    cuts = modify_cut(DEFAULT_CUTS, "dedx", min=1.5, max=3.0)
    df_sel = select(df, cuts=cuts)

**Drop a cut**::

    from cafpybara.core.selection import drop_cuts

    cuts = drop_cuts(DEFAULT_CUTS, "muon_rejection")
    cuts = drop_cuts(DEFAULT_CUTS, "direction", "shower_length")

**Add a custom cut**::

    from cafpybara.core.classes import CutSpec
    cuts = DEFAULT_CUTS + [CutSpec("my_cut", fn=lambda df: df.x > 10)]

**Adjust a parameter of an fn-based cut** (combine with ``functools.partial``)::

    from functools import partial
    cuts = modify_cut(DEFAULT_CUTS, "muon_rejection",
                      fn=partial(cut_muon_rejection, max_track_length=100))
"""

import warnings

import numpy as np
import pandas as pd
from dataclasses import replace
from functools import reduce

from .classes import CutSpec

__all__ = ['drop_cuts', 'modify_cut', 'select', 'union_cut', '_mask', '_and_mask']


# ---------------------------------------------------------------------------
# Cut application
# ---------------------------------------------------------------------------

def _mask(df, spec):
    """Return a boolean mask for spec applied to df."""
    if spec.fn is not None:
        return spec.fn(df)
    series = spec.accessor(df) if spec.accessor is not None else reduce(getattr, spec.variable, df)
    return (series > spec.min) & (series < spec.max)


def _and_mask(df, cuts):
    """AND a list of CutSpec masks, all evaluated against the same (unnarrowed) df."""
    mask = pd.Series(True, index=df.index)
    for spec in cuts:
        mask &= _mask(df, spec)
    return mask


def union_cut(name, cuts_a, cuts_b, label=None):
    """Build a single CutSpec that is the OR of two CutSpec chains.

    Lets a selection like "(1shw AND ...) OR (2shw AND ...)" be expressed as one
    CutSpec, so it folds into select()'s ordinary sequential-AND cuts= list (and
    therefore into load_mc/load_data/load_mchnl's load-time cuts= too) instead of
    needing a separate post-load union step.
    """
    return CutSpec(name, fn=lambda df: _and_mask(df, cuts_a) | _and_mask(df, cuts_b),
                    label=label or name)


def drop_cuts(cuts, *names):
    """Return a copy of cuts with the named cut(s) removed.

    Parameters
    ----------
    cuts : list of CutSpec
        The cut sequence to modify.
    *names : str
        Names of cuts to drop.

    Examples
    --------
    >>> cuts = drop_cuts(DEFAULT_CUTS, "muon_rejection")
    >>> cuts = drop_cuts(DEFAULT_CUTS, "direction", "shower_length")
    """
    unknown = set(names) - {c.name for c in cuts}
    if unknown:
        raise ValueError(f"No cuts named {sorted(unknown)}. Available: {[c.name for c in cuts]}")
    return [c for c in cuts if c.name not in names]


def modify_cut(cuts, name, **kwargs):
    """Return a copy of cuts with the named CutSpec updated.

    Parameters
    ----------
    cuts : list of CutSpec
        The cut sequence to modify.
    name : str
        Name of the cut to update.
    **kwargs
        Fields to update on the matching CutSpec (passed to
        ``dataclasses.replace``).

    Returns
    -------
    list of CutSpec
        New list with the named entry replaced.

    Raises
    ------
    ValueError
        If no cut with the given name exists.

    Examples
    --------
    >>> cuts = modify_cut(DEFAULT_CUTS, "dedx", min=1.5, max=3.0)
    >>> cuts = modify_cut(cuts, "muon_rejection",
    ...                   fn=partial(cut_muon_rejection, max_track_length=100))
    """
    names = [c.name for c in cuts]
    if name not in names:
        raise ValueError(f"No cut named '{name}'. Available: {names}")
    return [replace(c, **kwargs) if c.name == name else c for c in cuts]


# ---------------------------------------------------------------------------
# Selection pipeline
# ---------------------------------------------------------------------------

def select(indf,
           cuts,
           stage=None,
           savedict=False,
           check_preprocessed=True):
    """Apply a sequence of cuts to a DataFrame.

    Parameters
    ----------
    indf : pandas.DataFrame
        Input DataFrame. Must be preprocessed first -- call the relevant
        analysis's ``preprocess_*`` function before ``select()``.
    cuts : list of CutSpec
        Ordered cut sequence. No default -- pass an analysis's own cut list
        (e.g. ``nuecc.analysis.DEFAULT_CUTS``, ``hnlpi0.analysis.PI0_CUT_LISTS['1shw']``),
        or use :func:`modify_cut`/:func:`drop_cuts` to adjust one.
    stage : str, optional
        Stop and return after this cut (matched by ``CutSpec.name``).
    savedict : bool, default False
        If True, return a dict of DataFrames keyed by cut name instead
        of the final DataFrame.
    check_preprocessed : bool, default True
        If True, warn when no preprocessing fixes (``_fix_*`` columns)
        are detected on ``indf``. Suppress with ``check_preprocessed=False``
        for DataFrames where preprocessing is not applicable.

    Returns
    -------
    pandas.DataFrame or dict
        Final selected DataFrame, or per-stage dict when
        ``savedict=True`` or ``stage`` is set.
    """
    if cuts is None:
        raise ValueError(
            "select(): cuts is required -- there is no topology-wide default. "
            "Pass an analysis's own cut list (e.g. nuecc.analysis.DEFAULT_CUTS, "
            "hnlpi0.analysis.PI0_CUT_LISTS['1shw']), or use a per-analysis "
            "select() wrapper that supplies its own default."
        )

    if check_preprocessed:
        from .preprocess import applied_fixes
        if not applied_fixes(indf):
            warnings.warn(
                "No preprocessing fixes detected on this DataFrame. "
                "Call the relevant preprocess_* function before select().",
                stacklevel=2,
            )

    if stage is not None and stage not in {c.name for c in cuts}:
        raise ValueError(
            f"Unknown stage '{stage}'. Valid options: {[c.name for c in cuts]}"
        )

    df = indf.copy()

    df_dict = {}
    for spec in cuts:
        df = df[_mask(df, spec)]
        if savedict:
            df_dict[spec.name] = df
        if stage == spec.name:
            return df_dict if savedict else df

    return df_dict if savedict else df
