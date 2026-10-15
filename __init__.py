"""cafpybara: shared CAF-analysis toolkit (cafpyana + Python + capybara).

This top-level package intentionally does not re-export any names -- pick an
analysis by importing the corresponding subpackage directly, e.g.::

    import cafpybara.analyses.nuecc as ana
    import cafpybara.analyses.hnlpi0 as ana

Adding a new analysis topology means adding a new folder under
`cafpybara/analyses/`, mirroring cafpyana's own `analysis_village/` layout --
no shared registry or base class to edit.
"""

import os
import sys

CAFPYANA_PATH = os.environ.get("CAFPYANA_PATH")
if not CAFPYANA_PATH or not os.path.isdir(CAFPYANA_PATH):
    raise ImportError(
        f"CAFPYANA_PATH={CAFPYANA_PATH!r} is unset or not a directory -- "
        "export it (or set os.environ['CAFPYANA_PATH'] before importing "
        "cafpybara) to point at your cafpyana clone."
    )

if CAFPYANA_PATH not in sys.path:
    sys.path.append(CAFPYANA_PATH)
