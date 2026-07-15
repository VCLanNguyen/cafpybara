"""HNL/pi0 (nu_pi0) analysis -- built on cafpybara.core with this village's own defaults.

Usage::

    import cafpybara.analyses.hnlpi0 as ana

    df, pot, ngen = ana.load_mc("mc.df", cuts=ana.PI0_CUT_LISTS['1shw'],
                                 preprocess_fn=ana.preprocess_mcbnb)
    ana.plot_var(df, var, bins)

Re-exports the full flat namespace of the original (pre-refactor) package --
generic mechanics from ``cafpybara.core`` first, then this village's own
``analysis``/``io``/``plotting``/``funcs``/``bdt`` (which shadow the core
generics with HNL/pi0's own real defaults).
"""

from ... import core

# Generic mechanics from core, in the same order the original package's
# top-level __init__.py exported them.
from ...core.utils import *
from ...core.syst import *
from ...core.selection import *
from ...core.classes import *
from ...core.preprocess import *
from ...core.detvar import *

# This village's own config + thin wrappers/HNL-only content (shadow the core
# generics above with this topology's real defaults).
from . import config
from .analysis import *
from .preprocess import *
from .io import *
from .plotting import *
from .funcs import *
from . import bdt
