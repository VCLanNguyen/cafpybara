"""HNL/pi0's own preprocessing bundlers.

These build on the generic base/engines in :mod:`cafpybara.core.preprocess`
(``preprocess_mc``/``preprocess_data`` no-ops, ``fix_timing_calibration``)
plus this village's own generator-specific fixes and per-sample calibration
constants (:mod:`cafpybara.core.timing_calibration`'s ``mcbnb_*``/``mchnl_*``/
``offbeam_*`` constants).
"""
from __future__ import annotations

import pandas as pd

from ...core import timing_calibration as tc
from ...core.preprocess import (
    preprocess_mc, preprocess_data, fix_timing_calibration,
    fix_databnb_timing_calibration, add_variables,
    _skip_if_applied, _mark_applied,
)

__all__ = [
    'fix_bfm_flashtime_mcbnb', 'fix_bfm_flashtime_mchnl',
    'preprocess_mcbnb', 'preprocess_mchnl',
    'preprocess_databnb', 'preprocess_dataoff',
]


# ---------------------------------------------------------------------------
# Per-sample bugfixes
# ---------------------------------------------------------------------------

def fix_bfm_flashtime_mcbnb(df: pd.DataFrame) -> pd.DataFrame:
    """Correct the BFM flashTime reco offset for the BNB overlay generator (MC only).

    Wraps :func:`timing_calibration.bugfix_mcbnb_bfm_flashtime`. Call before
    :func:`~cafpybara.core.preprocess.fix_timing_calibration`. Applies to any
    BNB-overlay-generator sample (e.g. detvar CV/DV frames), not just mcbnb_df.
    """
    name = 'bfm_flashtime_mcbnb'
    if _skip_if_applied(df, name):
        return df
    df = tc.bugfix_mcbnb_bfm_flashtime(df)
    return _mark_applied(df, name)


def fix_bfm_flashtime_mchnl(df: pd.DataFrame) -> pd.DataFrame:
    """Correct the BFM flashTime reco offset for the MeVPrtl generator (MC only).

    Wraps :func:`timing_calibration.bugfix_mchnl_bfm_flashtime` -- a different
    fixed offset than :func:`fix_bfm_flashtime_mcbnb` (subtraction only, no extra
    beam-period term). Call before
    :func:`~cafpybara.core.preprocess.fix_timing_calibration`.
    """
    name = 'bfm_flashtime_mchnl'
    if _skip_if_applied(df, name):
        return df
    df = tc.bugfix_mchnl_bfm_flashtime(df)
    return _mark_applied(df, name)


# ---------------------------------------------------------------------------
# Bundled entry points
# ---------------------------------------------------------------------------

def preprocess_mcbnb(df: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`~cafpybara.core.preprocess.preprocess_mc` plus BNB overlay
    generator timing calibration.

    Adds :func:`fix_bfm_flashtime_mcbnb` and
    :func:`~cafpybara.core.preprocess.fix_timing_calibration`
    (``timing_calibration.mcbnb_period_calib``/``mcbnb_offset_calib``), plus
    ``add_variables`` (derived kinematic columns -- was a separate notebook
    "Add New Variables" step, now applied at load time like nueCC's convention).
    Also the correct call for any BNB-overlay-generator sample (e.g. detvar CV/DV
    frames), not just mcbnb_df.

    Parameters
    ----------
    df : pd.DataFrame
        MC DataFrame.
    """
    df = preprocess_mc(df)
    df = fix_bfm_flashtime_mcbnb(df)
    df = fix_timing_calibration(df, period=tc.mcbnb_period_calib, t0_offset=tc.mcbnb_offset_calib)
    df = add_variables(df)
    return df


def preprocess_mchnl(df: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`~cafpybara.core.preprocess.preprocess_mc` plus MeVPrtl generator
    timing calibration.

    Adds :func:`fix_bfm_flashtime_mchnl` and
    :func:`~cafpybara.core.preprocess.fix_timing_calibration`
    (``timing_calibration.mchnl_period_calib``/``mchnl_offset_calib``), plus
    ``add_variables`` (derived kinematic columns -- was a separate notebook
    "Add New Variables" step, now applied at load time like nueCC's convention).

    Parameters
    ----------
    df : pd.DataFrame
        MC DataFrame.
    """
    df = preprocess_mc(df)
    df = fix_bfm_flashtime_mchnl(df)
    df = fix_timing_calibration(df, period=tc.mchnl_period_calib, t0_offset=tc.mchnl_offset_calib)
    df = add_variables(df)
    return df


def preprocess_databnb(df: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`~cafpybara.core.preprocess.preprocess_data` plus real Data BNB's
    timing calibration.

    Adds :func:`~cafpybara.core.preprocess.fix_databnb_timing_calibration`
    (drops bad-period rows, corrects each good period individually), plus
    ``add_variables`` (derived kinematic columns -- was a separate notebook
    "Add New Variables" step, now applied at load time like nueCC's convention).

    Parameters
    ----------
    df : pd.DataFrame
        Data BNB DataFrame.
    """
    df = preprocess_data(df)
    df = fix_databnb_timing_calibration(df)
    df = add_variables(df)
    return df


def preprocess_dataoff(df: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`~cafpybara.core.preprocess.preprocess_data` plus Data
    Offbeam+Light timing calibration.

    Adds :func:`~cafpybara.core.preprocess.fix_timing_calibration`
    (``timing_calibration.offbeam_period_calib``/``offbeam_offset_calib``,
    ``ifData=True``), plus ``add_variables`` (derived kinematic columns -- was
    a separate notebook "Add New Variables" step, now applied at load time
    like nueCC's convention).

    Parameters
    ----------
    df : pd.DataFrame
        Data Offbeam+Light DataFrame.
    """
    df = preprocess_data(df)
    df = fix_timing_calibration(df, period=tc.offbeam_period_calib, t0_offset=tc.offbeam_offset_calib,
                                 ifData=True)
    df = add_variables(df)
    return df
