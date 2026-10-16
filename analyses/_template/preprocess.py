"""TEMPLATE -- your analysis's own preprocessing bundlers.

`core.preprocess.preprocess_mc`/`preprocess_data` are generic no-ops --
correct only if your topology genuinely needs no preprocessing.
Build a composite on top of them if it does; re-exporting the no-op
unchanged should be a deliberate decision, not an oversight.
"""
from __future__ import annotations

import pandas as pd

from ...core.preprocess import (
    preprocess_mc as _core_preprocess_mc,
    preprocess_data as _core_preprocess_data,
)

__all__ = ['preprocess_mc', 'preprocess_data']


def preprocess_mc(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- MC preprocessing for your topology.

    TODO: add your fixes (e.g. timing calibration, bugfixes).
    """
    df = _core_preprocess_mc(df)
    return df


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- data preprocessing for your topology.

    TODO: add your fixes (e.g. data-only timing calibration).
    """
    df = _core_preprocess_data(df)
    return df
