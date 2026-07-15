"""nueCC cross-section analysis -- built on cafpybara.core with nueCC's own defaults.

Usage::

    import cafpybara.analyses.nuecc as ana

    df, pot, ngen = ana.load_mc("mc.df", cuts=ana.DEFAULT_CUTS)
    ana.plot_var(df, var, bins)

Re-exports the full flat namespace of the original (pre-refactor) package --
generic mechanics from ``cafpybara.core`` first, then this village's own
``analysis``/``selection``/``io``/``plotting``/``funcs`` (which shadow the
core generics with nueCC's own real defaults, e.g. ``io.load_mc`` here
defaults ``rec_key='nuecc'`` where ``core.io.load_mc`` has no default at all).
"""

from ... import core

# Generic mechanics from core, in the same order the original package's
# top-level __init__.py exported them.
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

# This village's own config + thin wrappers (shadow the core generics above
# with nueCC's real defaults).
from . import config
from .analysis import *
from .preprocess import *
from .selection import *
from .io import *
from .plotting import *
from .funcs import *
from . import exclusive
