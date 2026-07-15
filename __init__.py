"""cafpybara: shared CAF-analysis toolkit (cafpyana + Python + capybara).

This top-level package intentionally does not re-export any names -- pick an
analysis by importing the corresponding subpackage directly, e.g.::

    import cafpybara.analyses.nuecc as ana
    import cafpybara.analyses.hnlpi0 as ana

Adding a new analysis topology means adding a new folder under
`cafpybara/analyses/`, mirroring cafpyana's own `analysis_village/` layout --
no shared registry or base class to edit.
"""

import sys

CAFPYANA_PATH = "/exp/sbnd/data/users/lnguyen/cafpyana_pi0/cafpyana"

if CAFPYANA_PATH not in sys.path:
    sys.path.append(CAFPYANA_PATH)
    sys.path.append(CAFPYANA_PATH + "/analysis_village")
