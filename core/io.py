"""File input/output utilities for loading HDF5 data files.

``load_mc``/``load_data`` here take no topology default for ``rec_key``,
``preprocess_fn``, or ``define_signal_fn``/``offbeam_signal_value`` -- every
analysis supplies its own via a thin wrapper in
``cafpybara/analyses/<topology>/io.py`` (e.g. nueCC's wrapper defaults
``rec_key='nuecc'``; HNL/pi0's defaults ``rec_key='rec'``).
"""
from __future__ import annotations

import gc

import numpy as np
import pandas as pd

__all__ = ['get_n_split', 'print_keys', 'load_dfs', 'load_mc', 'load_data']

_UNSET = object()

def get_n_split(file):
    """Get the number of splits in an HDF5 file.

    Parameters
    ----------
    file : str
        Path to HDF5 file.

    Returns
    -------
    int
        Number of splits in the file.
    """
    this_split_df = pd.read_hdf(file, key="split")
    this_n_split = this_split_df.n_split.iloc[0]
    return this_n_split

def print_keys(file):
    """Print all keys available in an HDF5 file.

    Parameters
    ----------
    file : str
        Path to HDF5 file.
    """
    with pd.HDFStore(file, mode='r') as store:
        keys = store.keys()
        print("Keys:", keys)

def load_dfs(file, keys2load, n_max_concat=10, start_split=0):
    """Load DataFrames from split HDF5 file.

    Parameters
    ----------
    file : str
        Path to HDF5 file.
    keys2load : list
        List of key names to load from the file.
    n_max_concat : int, optional
        Maximum number of splits to concatenate (default: 10).
    start_split : int, optional
        Starting split index to load from (default: 0).

    Returns
    -------
    dict
        Dictionary mapping key names to concatenated DataFrames.
    """
    out_df_dict = {}
    with pd.HDFStore(file, mode='r') as store:
        this_n_keys = store['split'].n_split.iloc[0] - start_split
        n_concat = min(n_max_concat, this_n_keys)
        for key in keys2load:
            dfs = [store[f'{key}_{i}'] for i in range(start_split, start_split + n_concat)]
            out_df_dict[key] = pd.concat(dfs, ignore_index=False)
    return out_df_dict


# ---------------------------------------------------------------------------
# High-level loaders
# ---------------------------------------------------------------------------

def load_mc(
    file: str,
    rec_key: str,
    preprocess_fn,
    define_signal_fn,
    keys: list | None = None,
    cuts=None,
    max_splits: int | None = None,
    chunk_splits: int = 1,
    add_pi0_fn=None,
    excl_mc_df=None,
    remove_signal_overlap_fn=None,
) -> tuple:
    """Load, preprocess, and optionally select an MC HDF5 file in chunks.

    Splits are loaded in batches of chunk_splits to balance memory and I/O
    overhead.  POT and generated-event counts are accumulated across all
    splits.  Header columns (run/subrun/event) are merged into the output
    DataFrame.

    Parameters
    ----------
    file : str
        Path to the HDF5 file.
    rec_key : str
        Key of the main slc-level table within ``keys``/the HDF5 file (e.g.
        ``'nuecc'`` or ``'rec'``). Required -- no topology default here.
    preprocess_fn : callable or None
        Called as ``preprocess_fn(df)`` on each chunk's ``rec_key`` table
        before selection. Pass ``None`` to skip preprocessing entirely.
        Required (explicitly, even if None) -- no topology default here.
    define_signal_fn : callable
        Called as ``define_signal_fn(df)`` on each merged chunk to stamp
        signal categories (e.g.
        ``functools.partial(nuecc.analysis.define_signal, prefix=('slc', 'truth'))``
        or ``hnlpi0.selection.define_signal_hnl``).
        Required -- no topology default here.
    keys : list of str, optional
        Table keys to load.  Defaults to
        ``['hdr', rec_key, 'histpotdf', 'histgenevtdf']``.
    cuts : list of CutSpec, optional
        If supplied, passed to :func:`~cafpybara.core.selection.select`.
        When None the full preprocessed DataFrame is returned.
    max_splits : int, optional
        Cap on the number of splits to load.  Defaults to all splits.
    chunk_splits : int, default 1
        Number of splits to load per iteration.  Increase to reduce I/O
        overhead at the cost of higher peak memory per chunk.
    add_pi0_fn : callable, optional
        If given, called as ``add_pi0_fn(df)`` on each chunk after preprocessing
        to compute pi0 kinematics.
    excl_mc_df : pd.DataFrame, optional
        Exclusive DataFrame with signal categorisation already applied (i.e.
        has a top-level ``signal`` column).  When provided,
        ``remove_signal_overlap_fn`` is called on the final concatenated
        result to strip events that are already covered by the exclusive
        sample and would otherwise be double-counted.
    remove_signal_overlap_fn : callable, optional
        Called as ``remove_signal_overlap_fn(result, excl_mc_df)`` when
        ``excl_mc_df`` is provided. Required if ``excl_mc_df`` is not None.

    Returns
    -------
    df : pd.DataFrame
        Concatenated, preprocessed (and optionally selected) MC DataFrame
        with header columns merged in and signal categories defined.
    pot : float
        Accumulated POT.
    ngen : float
        Accumulated generated-event count.
    """
    try:
        from tqdm import tqdm as _tqdm
    except ImportError:
        _tqdm = None

    from .selection import select
    from .utils import merge_hdr

    if keys is None:
        keys = ['hdr', rec_key, 'histpotdf', 'histgenevtdf']

    n_total  = get_n_split(file)
    n_splits = min(max_splits, n_total) if max_splits is not None else n_total
    starts   = range(0, n_splits, chunk_splits)
    iterator = _tqdm(starts) if _tqdm is not None else starts

    pot    = 0.0
    ngen   = 0.0
    chunks = []

    for i in iterator:
        n_load = min(chunk_splits, n_splits - i)
        dfs = load_dfs(file, keys2load=keys, n_max_concat=n_load, start_split=i)

        if 'histpotdf' in dfs:    pot  += dfs['histpotdf'].TotalPOT.sum()
        elif 'hdr' in dfs:        pot  += dfs['hdr'].pot.sum()
        if 'histgenevtdf' in dfs: ngen += dfs['histgenevtdf'].TotalGenEvents.sum()
        elif 'hdr' in dfs:        ngen += dfs['hdr'][dfs['hdr'].first_in_subrun == 1].ngenevt.sum()

        df    = preprocess_fn(dfs[rec_key]) if preprocess_fn is not None else dfs[rec_key]
        sel   = select(df, cuts=cuts) if cuts is not None else df
        chunk = merge_hdr(dfs['hdr'], sel)
        del dfs
        chunk = define_signal_fn(chunk)
        if add_pi0_fn is not None:
            chunk = add_pi0_fn(chunk)
        chunks.append(chunk)
        del chunk
        gc.collect()

    result = pd.concat(chunks, ignore_index=False).copy()
    if excl_mc_df is not None:
        if remove_signal_overlap_fn is None:
            raise ValueError("load_mc: excl_mc_df was given but remove_signal_overlap_fn is None")
        result = remove_signal_overlap_fn(result, excl_mc_df)
    return result, pot, ngen


def load_data(
    file: str,
    rec_key: str,
    preprocess_fn,
    keys: list | None = None,
    onbeam: bool = True,
    cuts=None,
    offbeam_signal_value=_UNSET,
) -> tuple:
    """Load, preprocess, and optionally select a data HDF5 file.

    Parameters
    ----------
    file : str
        Path to the HDF5 file.
    rec_key : str
        Key of the main slc-level table within ``keys``/the HDF5 file (e.g.
        ``'nuecc'`` or ``'rec'``). Required -- no topology default here.
    preprocess_fn : callable or None
        Called as ``preprocess_fn(df)`` on the merged table before selection.
        Pass ``None`` to skip preprocessing entirely. Required (explicitly,
        even if None) -- no topology default here.
    keys : list of str, optional
        Table keys to load.  Defaults to ``['hdr', rec_key, 'histpotdf']``.
    onbeam : bool, default True
        True for on-beam (BNB) data; False for off-beam.  Controls which
        gate counter is returned and whether the offbeam signal category is
        stamped on the output DataFrame.
    cuts : list of CutSpec, optional
        If supplied, passed to :func:`~cafpybara.core.selection.select`.
        When None the full preprocessed DataFrame is returned.
    offbeam_signal_value : int, required if onbeam=False
        Signal value stamped on off-beam rows when ``onbeam=False`` (e.g.
        ``nuecc.analysis.signal_dict['offbeam']`` or
        ``hnlpi0.analysis.signal_dict_hnl['offbeam']``). No topology default.

    Returns
    -------
    df : pd.DataFrame
        Preprocessed (and optionally selected) data DataFrame with header
        columns merged in.  Off-beam DataFrames also have ``signal`` set to
        ``offbeam_signal_value``.
    pot : float
        Accumulated on-beam POT (0.0 for off-beam files).
    ngates : float
        BNB gate count (on-beam) or off-beam gate count.
    """
    from pyanalib.pandas_helpers import multicol_add
    from .selection import select
    from .utils import merge_hdr

    if keys is None:
        keys = ['hdr', rec_key, 'histpotdf']
    if not onbeam and offbeam_signal_value is _UNSET:
        raise ValueError("load_data: offbeam_signal_value is required when onbeam=False")

    dfs = load_dfs(file, keys2load=keys)
    df  = merge_hdr(dfs['hdr'], dfs[rec_key])
    df  = preprocess_fn(df) if preprocess_fn is not None else df

    pot    = 0.0
    ngates = 0.0
    if onbeam:
        pot    = dfs['histpotdf'].TotalPOT.sum() if 'histpotdf' in dfs else dfs['hdr'].pot.sum()
        ngates = dfs['hdr'].nbnbinfo.sum()
    else:
        ngates = dfs['hdr'].noffbeambnb.sum()
        signal = pd.Series(
            np.ones(len(df), dtype=np.int16) * offbeam_signal_value,
            name="signal", index=df.index,
        )
        df = multicol_add(df, signal)

    sel = select(df, cuts=cuts) if cuts is not None else df
    return sel, pot, ngates
