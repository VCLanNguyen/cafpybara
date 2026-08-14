"""HNL/pi0 -- per-analysis wiring for core/detvar/process_detvars.py."""

from . import preprocess
from . import analysis

SLC_KEY = "rec"

DEFAULT_PREPROCESS_FN = preprocess.preprocess_mcbnb

SELECTION_FN_MAP = {
    "1shw": (analysis.PI0_CUT_LISTS['1shw'], None),
}
