"""HNL/pi0's own load_mc()/load_data()/load_mchnl().

``load_mc``/``load_data`` pre-fill :func:`cafpybara.core.io.load_mc`/
``load_data`` with this village's own ``rec_key='rec'`` and truth-signal
categorisation. ``load_mchnl`` is entirely HNL/pi0-specific (MeVPrtl
generator loading) and has no core-generic equivalent -- no other topology
has an analogous sample type.
"""
from __future__ import annotations

from functools import partial

import numpy as np
import pandas as pd

from ...core.io import load_mc as _core_load_mc, load_data as _core_load_data, load_dfs, get_n_split
from ...core.preprocess import preprocess_mc, preprocess_data
from ...core.selection import select
from .analysis import define_signal_pi0, define_signal_hnl, signal_dict_hnl

__all__ = ['load_mc', 'load_data', 'load_mchnl', 'correct_cosmic_weight_mevprtl_df']

_define_signal_fn = partial(define_signal_pi0, prefix=('slc', 'truth'))


def load_mc(
    file: str,
    keys: list | None = None,
    cuts=None,
    max_splits: int | None = None,
    chunk_splits: int = 1,
    add_pi0: bool = False,
    excl_mc_df=None,
    rec_key: str = 'rec',
    preprocess_fn=preprocess_mc,
    define_signal_fn=_define_signal_fn,
):
    """Load an MC HDF5 file. See :func:`cafpybara.core.io.load_mc` for full docs.

    Defaults match this village's historical behavior: ``rec_key='rec'``,
    ``preprocess_fn=preprocess_mc`` (base, currently a no-op -- pass e.g.
    ``preprocess_mcbnb`` explicitly for real timing calibration),
    ``define_signal_fn`` stamps this village's own ``define_signal_pi0``.
    """
    from ...core.preprocess import add_pi0 as _add_pi0
    add_pi0_fn = _add_pi0 if add_pi0 else None
    return _core_load_mc(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_fn,
        keys=keys, cuts=cuts, max_splits=max_splits, chunk_splits=chunk_splits,
        add_pi0_fn=add_pi0_fn, excl_mc_df=excl_mc_df,
    )


def load_data(
    file: str,
    keys: list | None = None,
    onbeam: bool = True,
    cuts=None,
    rec_key: str = 'rec',
    preprocess_fn=preprocess_data,
    offbeam_signal_value=None,
):
    """Load a data HDF5 file. See :func:`cafpybara.core.io.load_data` for full docs.

    Defaults match this village's historical behavior: ``rec_key='rec'``,
    ``preprocess_fn=preprocess_data`` (base, currently a no-op),
    ``offbeam_signal_value=signal_dict_hnl['offbeam']``.
    """
    if not onbeam and offbeam_signal_value is None:
        offbeam_signal_value = signal_dict_hnl['offbeam']
    return _core_load_data(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn,
        keys=keys, onbeam=onbeam, cuts=cuts, offbeam_signal_value=offbeam_signal_value,
    )


def correct_cosmic_weight_mevprtl_df(indf_rec, indf_truth, indf_hdr):
    """Correct the cosmic-background event weight in an HNL MeVPrtl reco DataFrame
    using the matching truth-level total weight.

    Reco and truth don't share a common natural row index -- their sub-object index
    levels differ (``rec.slc..index`` vs. ``rec.mc.prtl..index``) -- so they're joined
    via a composite key built from ``evt`` (looked up per-row from the header table)
    instead of the natural index.

    When present, ``file_idx`` is included in that composite key alongside
    ``(__ntuple, entry, evt)``. This matters for any file produced by
    ``concat_hdf.py``: it resets ``__ntuple``/``entry`` numbering independently per
    source shard and adds a ``file_idx`` level specifically to disambiguate the
    result, so omitting ``file_idx`` from the join key causes rows from different
    shards to collide on the same ``(__ntuple, entry, evt)`` triple -- ``reindex``
    then raises ``ValueError: cannot handle a non-unique multi-index`` (this crashed
    on any concatenated multi-shard HNL sample prior to this fix; verified against
    the real ``mchnl_nupi0_m260.df``, 15 shards). Falls back to the
    ``(__ntuple, entry, evt)``-only key when ``file_idx`` isn't present on either
    side, matching the original behaviour for a raw, non-concatenated single-shard
    file.

    Parameters
    ----------
    indf_rec : pd.DataFrame
        HNL reco (slice-level) DataFrame.
    indf_truth : pd.DataFrame
        HNL MeVPrtl truth DataFrame.
    indf_hdr : pd.DataFrame
        Header DataFrame, used to look up ``evt`` for both ``indf_rec`` and
        ``indf_truth``.
    """

    #Step 1: Build total event weight in reco and truth HNL dataframes

    # Build total event weight in reco and truth HNL dataframes
    fluxw_column = ('slc', 'prtl', 'flux_weight', '', '', '')
    rayw_column = ('slc', 'prtl', 'ray_weight', '', '', '')
    decayw_column = ('slc', 'prtl', 'decay_weight', '', '', '')
    totalw_column = ('weights_mc', '', '', '', '', '')
    indf_rec[totalw_column] = indf_rec[rayw_column] * indf_rec[decayw_column] * indf_rec[fluxw_column]

    truth_fluxw_column = ('flux_weight', '')
    truth_rayw_column = ('ray_weight', '')
    truth_decayw_column = ('decay_weight', '')
    truth_totalw_column = ('weights_mc_truth', '')
    indf_truth[truth_totalw_column] = indf_truth[truth_rayw_column] * indf_truth[truth_decayw_column] * indf_truth[truth_fluxw_column]

    #-------------------------------------------------------------------------------------#
    #Step 2: Join evt from header dataframe into reco dataframe using reco's own full index
    evt_col = ('evt', '', '', '', '', '')
    indf_rec[evt_col] = indf_hdr['evt'].reindex(indf_rec.index)

    #-------------------------------------------------------------------------------------#
    # Step 3: Join truth total weight into reco dataframe on (file_idx, __ntuple, entry, evt)
    # -- file_idx included only when present on both sides, see docstring.
    totalw_truth_col = ('weights_mc_truth', '', '', '', '', '')

    truth_total_weight = indf_truth[truth_totalw_column]
    truth_evt = indf_hdr['evt'].reindex(indf_truth.index).values

    join_levels = ['__ntuple', 'entry']
    if 'file_idx' in indf_truth.index.names and 'file_idx' in indf_rec.index.names:
        join_levels = ['file_idx'] + join_levels
    join_names = join_levels + ['evt']

    truth_key = pd.MultiIndex.from_arrays(
        [indf_truth.index.get_level_values(lvl) for lvl in join_levels] + [truth_evt],
        names=join_names,
    )
    truth_lookup = pd.Series(truth_total_weight.values, index=truth_key)

    reco_key = pd.MultiIndex.from_arrays(
        [indf_rec.index.get_level_values(lvl) for lvl in join_levels] + [indf_rec[evt_col].values],
        names=join_names,
    )

    # .map() instead of Series.reindex(): a direct lookup against reco_key's own order
    # rather than reindex's stricter re-alignment machinery -- same result, cheaper
    # since it doesn't need to build/validate reco_key as a standalone index in its
    # own right the way reindex does.
    indf_rec[totalw_truth_col] = reco_key.map(truth_lookup)

    #-------------------------------------------------------------------------------------#
    # Step 4: Correct cosmic weight in reco dataframe using truth total weight for cosmic entries

    mask_cosmic = np.isnan(indf_rec[('slc', 'prtl', 'E', '', '', '')])
    indf_rec.loc[mask_cosmic, totalw_column] = indf_rec.loc[mask_cosmic, truth_totalw_column]

    #-------------------------------------------------------------------------------------#
    #Drop event column from reco dataframe
    indf_rec = indf_rec.drop(columns=[evt_col])

    return indf_rec


def load_mchnl(
    file: str,
    keys: list | None = None,
    mevprtl_key: str = 'mevprtl',
    rec_key: str = 'rec',
    cuts=None,
    preprocess_fn=preprocess_mc,
) -> tuple:
    """Load and preprocess an HNL MeVPrtl MC HDF5 file.

    Applies the MeVPrtl-specific cosmic-weight correction
    (:func:`correct_cosmic_weight_mevprtl_df`), stamps HNL signal categories
    (:func:`~cafpybara.analyses.hnlpi0.analysis.define_signal_hnl`), and merges
    header columns in. Also extracts the simulated mixing angle and HNL mass
    from the truth table, since every HNL sample needs these for
    scaling/labeling.

    Parameters
    ----------
    file : str
        Path to the HDF5 file.
    keys : list of str, optional
        Table keys to load, not including ``mevprtl_key`` (added automatically
        if missing). Defaults to ``['hdr', rec_key, 'histpotdf']``.
    mevprtl_key : str, default 'mevprtl'
        Key of the MeVPrtl truth table.
    rec_key : str, default 'rec'
        Key of the main slc-level table.
    cuts : list of CutSpec, optional
        If supplied, passed to :func:`~cafpybara.core.selection.select` as the
        last step, after ``simU``/``hnlM`` are extracted from the full
        (unselected) DataFrame -- selection can otherwise remove every
        truth-matched row and make that extraction raise. When None the full
        preprocessed DataFrame is returned.
    preprocess_fn : callable or None, optional
        Called as ``preprocess_fn(df)`` on the raw ``rec_key`` table before the
        cosmic-weight correction. Defaults to the base (no-op)
        ``preprocess_mc`` -- pass ``preprocess_mchnl`` explicitly for real
        timing calibration. Pass ``None`` to skip.

    Returns
    -------
    df : pd.DataFrame
        Preprocessed (and optionally selected) HNL DataFrame with header
        columns merged in and signal categories defined.
    pot : float
        HNL MC POT (unscaled).
    info : dict
        ``{'simU': ..., 'hnlM': ...}`` -- simulated mixing angle squared and
        HNL mass in MeV (already converted from the truth table's GeV),
        extracted from the truth table. Build a legend label from these at
        the call site -- exact wording/formatting varies by analysis, so it
        isn't baked in here.
    """
    from ...core.utils import merge_hdr

    if keys is None:
        keys = ['hdr', rec_key, 'histpotdf']
    load_keys = keys if mevprtl_key in keys else keys + [mevprtl_key]

    # load_dfs defaults to n_max_concat=10 -- silently loads only the first 10 HDF5
    # splits if not told otherwise. Pass the file's actual split count explicitly so
    # a future mchnl production with more than 10 splits doesn't get silently
    # truncated here.
    dfs = load_dfs(file, keys2load=load_keys, n_max_concat=get_n_split(file))
    rec_df = preprocess_fn(dfs[rec_key]) if preprocess_fn is not None else dfs[rec_key]
    df  = correct_cosmic_weight_mevprtl_df(rec_df, dfs[mevprtl_key], dfs['hdr'])
    df  = define_signal_hnl(df)
    df  = merge_hdr(dfs['hdr'], df)

    pot  = dfs['histpotdf'].TotalPOT.sum() if 'histpotdf' in dfs else dfs['hdr'].pot.sum()
    simU = df[('slc', 'prtl', 'C2', '', '', '')].dropna().unique()[0]
    hnlM = df[('slc', 'prtl', 'M', '', '', '')].dropna().unique()[0] * 1000  # GeV -> MeV

    sel = select(df, cuts=cuts) if cuts is not None else df
    return sel, pot, {'simU': simU, 'hnlM': hnlM}
