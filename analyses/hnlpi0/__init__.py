"""HNL/pi0 (nu_pi0) analysis -- built on cafpybara.core with this analysis's own defaults.

Usage::

    import cafpybara.analyses.hnlpi0 as ana

    df, pot, ngen = ana.load_mc("mc.df", cuts=ana.PI0_CUT_LISTS['1shw'],
                                 preprocess_fn=ana.preprocess_mcbnb)
    ana.plot_var(df, var, bins)

Re-exports the full flat namespace of the original (pre-refactor) package --
generic mechanics from ``cafpybara.core`` first, then this analysis's own
``analysis``/``io``/``plotting``/``funcs``/``bdt`` (which shadow the core
generics with HNL/pi0's own real defaults).
"""

from ... import core

from ...core.utils import *
from ...core.io import *
from ...core.plotting import *
from ...core.physics import *
from ...core.syst import *
from ...core.selection import *
from ...core.classes import *
from ...core.funcs import *
from ...core.preprocess import *
from ...core.detvar import *

from . import config
from .analysis import *
from .preprocess import *
from .io import *
from .plotting import *
from .funcs import *
from . import bdt
