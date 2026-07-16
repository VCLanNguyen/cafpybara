"""TEMPLATE -- your analysis's own signal categories and cut sequence.

Shared/generic pieces (physical constants, generic_categories,
pdg_categories, mode_categories, category_dict_signal/control) already live
in :mod:`cafpybara.core.physics` -- this file should hold only what's
genuinely specific to your topology, the same split hnlpi0/nuecc use.

Everything below is a TOY example, not a real cut sequence -- it imports
and runs (against a DataFrame with the right columns), but the actual
column names/thresholds are illustrative. Replace with your topology's
real selection.
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

# TODO: set your real signal/background categories (unique 'value',
# display 'label', plot 'color' per entry).
signal_categories = {
    "signal":  {"value": 0, "label": "Signal",       "color": "#E7004C"},
    "other":   {"value": 1, "label": "Other",        "color": "#005A8F"},
    "nonFV":   {"value": 2, "label": "Non-FV",        "color": "#FF9664"},
    "cosmic":  {"value": 3, "label": "Cosmic",        "color": "#708090"},
}
signal_dict = {k: v["value"] for k, v in signal_categories.items()}


# ---------------------------------------------------------------------------
# Cut sequence
# ---------------------------------------------------------------------------

# TODO: set your real cut sequence (CutSpec: threshold `variable=`/`min=`/
# `max=`, or a full `fn=` mask).
DEFAULT_CUTS = [
    CutSpec("example_threshold_cut", variable=("slc", "example_score"), min=0.5,
            label="example_score > 0.5"),
    CutSpec("example_fn_cut", fn=lambda df: df.slc.n_trks == 0,
            label="no reconstructed tracks"),
]


# ---------------------------------------------------------------------------
# Truth categorisation
# ---------------------------------------------------------------------------

def define_signal(indf: pd.DataFrame, prefix=None) -> pd.DataFrame:
    """TEMPLATE -- stamp a 'signal' column using `signal_dict` above.

    TODO: set your real truth-level categorisation logic.
    """
    from ...core.utils import ensure_lexsorted

    nudf = ensure_lexsorted(ensure_lexsorted(indf, 0), 1)
    mcdf = nudf if prefix is None else nudf[prefix]

    signal = np.full(len(nudf), signal_dict["other"], dtype=np.int16)
    # TODO: real conditions go here, e.g.:
    # signal[some_signal_condition] = signal_dict["signal"]
    nudf["signal"] = signal
    return nudf
