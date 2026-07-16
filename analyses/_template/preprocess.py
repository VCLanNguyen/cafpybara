"""TEMPLATE -- your analysis's own preprocessing bundlers.

`core.preprocess.preprocess_mc`/`preprocess_data` are generic no-ops --
correct only if your topology genuinely needs no real preprocessing.
Build a real composite on top of them if it does; re-exporting the no-op
unchanged should be a deliberate decision, not an oversight.
"""
from __future__ import annotations

import pandas as pd

from ...core.preprocess import preprocess_mc, preprocess_data, add_variables

__all__ = ['preprocess_mc_real', 'preprocess_data_real']


def preprocess_mc_real(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- real MC preprocessing for your topology.

    TODO: add your real fixes (timing calibration, generator bugfixes,
    ...) before/after `add_variables`.
    """
    df = preprocess_mc(df)
    df = add_variables(df)
    return df


def preprocess_data_real(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- real data preprocessing for your topology.

    TODO: add your real fixes (e.g. data-only timing calibration).
    """
    df = preprocess_data(df)
    df = add_variables(df)
    return df
