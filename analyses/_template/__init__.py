"""TEMPLATE analysis -- not a real, usable analysis. Copy this directory to
start a new one; don't import it directly.

Usage (once you've copied this into e.g. `analyses/myanalysis/` and filled
in the TODOs)::

    import cafpybara.analyses.myanalysis as ana
    df, pot, ngen = ana.load_mc("mc.df", cuts=ana.DEFAULT_CUTS)
    ana.plot_var(df, var, bins)

Re-exports the full flat namespace: generic mechanics from
``cafpybara.core`` first, then this analysis's own
``analysis``/``preprocess``/``io``/``plotting``/``funcs`` (which shadow the
core generics with this analysis's own real defaults). Getting this
re-export block exactly right, unmodified, is more important than it looks
-- see `examples/build_a_new_analysis.ipynb`'s first section for why: two
real bugs this project has already hit (missing `core.io`/`funcs`/
`plotting`/`selection`/`physics` re-exports) were exactly a version of this
file with one of these lines missing.
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
