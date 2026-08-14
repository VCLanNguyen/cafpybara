"""nueCC -- per-analysis wiring for core/detvar/process_detvars.py."""

from . import preprocess
from . import analysis

SLC_KEY = "nuecc"

DEFAULT_PREPROCESS_FN = preprocess.preprocess_mc

SELECTION_FN_MAP = {
    "signal":    (analysis.DEFAULT_CUTS, None),
    "sideband":  (analysis.SIDEBAND_CUTS, None),
    "preselect": (analysis.DEFAULT_CUTS, "shower_energy"),
}
