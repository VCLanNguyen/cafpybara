"""TEMPLATE -- your analysis's own signal categories and cut sequence.

Shared/generic pieces (physical constants, generic_categories,
pdg_categories, mode_categories, category_dict_signal/control) already live
in :mod:`cafpybara.core.physics` -- this file should hold only what's
genuinely specific to your topology, the same split hnlpi0/nuecc use.

`signal_categories`/`define_signal` below give the minimal real split
every analysis needs (neutrino vs. cosmic); `DEFAULT_CUTS` starts empty.
Add your own topology-specific categories/cuts on top.
"""

import numpy as np
import pandas as pd

from ...core.classes import CutSpec
from ...core.selection import select

__all__ = [
    'signal_categories', 'signal_dict', 'DEFAULT_CUTS', 'define_signal',
]


# ---------------------------------------------------------------------------
# Signal/background category definitions
# ---------------------------------------------------------------------------

# TODO: set your signal/background categories (unique 'value',
# display 'label', plot 'color' per entry).
signal_categories = {
    "signal":  {"value": 0, "label": "Neutrino", "color": "#E7004C"},
    "cosmic":  {"value": 1, "label": "Cosmic",   "color": "#708090"},
}
signal_dict = {k: v["value"] for k, v in signal_categories.items()}


# ---------------------------------------------------------------------------
# Truth categorisation
# ---------------------------------------------------------------------------

def define_signal(indf: pd.DataFrame, prefix=None) -> pd.DataFrame:
    """TEMPLATE -- stamp a 'signal' column using `signal_dict` above.

    TODO: split `signal_categories` further for your topology.
    """
    from ...core.utils import ensure_lexsorted

    nudf = ensure_lexsorted(ensure_lexsorted(indf, 0), 1)
    mcdf = nudf if prefix is None else nudf[prefix]

    is_cosmic = np.isnan(mcdf.E)
    nudf["signal"] = np.where(is_cosmic, signal_dict["cosmic"], signal_dict["signal"]).astype(np.int16)
    return nudf


# ---------------------------------------------------------------------------
# Cut sequence
# ---------------------------------------------------------------------------

# TODO: set your cut sequence (CutSpec: threshold `variable=`/`min=`/
# `max=`, or a full `fn=` mask).
DEFAULT_CUTS = [
    CutSpec("clear_cosmic", fn=lambda df: df.slc.is_clear_cosmic == 0,
            label="not clear cosmic"),
    CutSpec("nu_score", variable=("slc", "nu_score"), min=0.5,
            label="nu score > 0.5"),
]
