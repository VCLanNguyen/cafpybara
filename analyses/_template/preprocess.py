"""TEMPLATE -- your analysis's own preprocessing bundlers.

This is the single most consequential file to get right in the whole
template. `core.preprocess.preprocess_mc`/`preprocess_data` are
deliberately generic no-ops -- correct for a topology that genuinely needs
no real preprocessing, but WRONG if your topology needs real fixes
(timing calibration, flash-PE rescaling, derived kinematic variables,
...) and this file just re-exports the no-op instead of building a real
composite on top of it.

That exact mistake happened twice in this project already (nueCC's
load_mc/load_data wired to core's no-op instead of nueCC's real fixes;
then the identical bug found again in hnlpi0.load_mchnl) -- see
`examples/build_a_new_analysis.ipynb`'s preprocessing section for the full
story of both. If your topology genuinely needs no preprocessing beyond
the generic base, it's fine to just re-export `preprocess_mc`/
`preprocess_data` unchanged -- just make that a deliberate decision, not
an oversight.
"""
from __future__ import annotations

import pandas as pd

from ...core.preprocess import preprocess_mc, preprocess_data, add_variables

__all__ = ['preprocess_mc_real', 'preprocess_data_real']


def preprocess_mc_real(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- real MC preprocessing for your topology.

    TODO: replace/extend this with your topology's actual fixes (timing
    calibration, generator-specific bugfixes, ...). `add_variables` here
    adds the generic derived kinematic columns every topology needs; if you
    have topology-specific derived columns, add them after it, following
    hnlpi0.preprocess.preprocess_mcbnb's shape.
    """
    df = preprocess_mc(df)
    df = add_variables(df)
    return df


def preprocess_data_real(df: pd.DataFrame) -> pd.DataFrame:
    """TEMPLATE -- real data preprocessing for your topology.

    TODO: replace/extend this with your topology's actual fixes (e.g. a
    real-data-only timing calibration, following
    hnlpi0.preprocess.preprocess_databnb's shape).
    """
    df = preprocess_data(df)
    df = add_variables(df)
    return df
