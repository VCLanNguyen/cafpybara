"""nueCC's own preprocessing bundlers.

Unlike HNL/pi0, nueCC's MC/data preprocessing is *not* a no-op -- it applies
real fixes (flash timing/PE calibration, primary+secondary shower energy,
derived phi angles) built from the generic pieces in
:mod:`cafpybara.core.preprocess`. Found live: the initial build wrongly
assumed nueCC's own ``preprocess_mc``/``preprocess_data`` were no-ops (true
on a different, HNL-focused branch of the ancestor repo, not on the nueCC
`master` branch this analysis is meant to match) -- every MC/data dataframe
loaded via ``nuecc.load_mc``/``load_data`` was silently skipping these fixes
until this file was added.
"""
from __future__ import annotations

import pandas as pd

from ...core.preprocess import (
    fix_flash_pe_scale, fix_flash_time, fix_prim_shw_energy,
    fix_sec_shw_energy, add_phi,
)

__all__ = ['preprocess_mc', 'preprocess_data']


def preprocess_mc(df: pd.DataFrame, *, flash_pe_scale: float = 0.66) -> pd.DataFrame:
    """Apply all standard MC preprocessing fixes in order.

    Applies:

    1. :func:`~cafpybara.core.preprocess.fix_flash_pe_scale`  — flash PE calibration correction
    2. :func:`~cafpybara.core.preprocess.fix_prim_shw_energy` — primary shower reco_energy from maxplane_energy
    3. :func:`~cafpybara.core.preprocess.fix_sec_shw_energy`  — secondary shower energy from maxplane_energy
    4. :func:`~cafpybara.core.preprocess.add_phi`             — shower and track azimuthal angles

    All fixes are idempotent; calling this on an already-preprocessed
    DataFrame is safe (each already-applied fix warns and skips).

    Parameters
    ----------
    df : pd.DataFrame
        MC DataFrame.
    flash_pe_scale : float
        Scale factor forwarded to :func:`~cafpybara.core.preprocess.fix_flash_pe_scale` (default 0.66).
    """
    df = fix_flash_pe_scale(df, scale=flash_pe_scale)
    df = fix_prim_shw_energy(df)
    df = fix_sec_shw_energy(df)
    df = add_phi(df)
    return df


def preprocess_data(df: pd.DataFrame, *, flash_time_offset: float = 0.19) -> pd.DataFrame:
    """Apply all standard data preprocessing fixes in order.

    Applies:

    1. :func:`~cafpybara.core.preprocess.fix_flash_time`      — flash time frame-offset correction
    2. :func:`~cafpybara.core.preprocess.fix_prim_shw_energy` — primary shower reco_energy from maxplane_energy
    3. :func:`~cafpybara.core.preprocess.fix_sec_shw_energy`  — secondary shower energy from maxplane_energy
    4. :func:`~cafpybara.core.preprocess.add_phi`             — shower and track azimuthal angles

    All fixes are idempotent; calling this on an already-preprocessed
    DataFrame is safe (each already-applied fix warns and skips).

    Parameters
    ----------
    df : pd.DataFrame
        Data DataFrame (on-beam or off-beam).
    flash_time_offset : float
        Timing offset in µs forwarded to :func:`~cafpybara.core.preprocess.fix_flash_time` (default 0.19).
    """
    df = fix_flash_time(df, offset=flash_time_offset)
    df = fix_prim_shw_energy(df)
    df = fix_sec_shw_energy(df)
    df = add_phi(df)
    return df
