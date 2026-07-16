"""nueCC's own select()/select_sideband() convenience wrappers.

Unlike :func:`cafpybara.core.selection.select`, ``cuts`` here defaults to
nueCC's own ``DEFAULT_CUTS``/``SIDEBAND_CUTS`` -- matching this analysis's
historical, actually-relied-upon behavior (nueCC's own example notebooks
call ``select()``/``get_total_cov()`` without always specifying ``cuts=``
explicitly).
"""

from ...core.selection import select as _core_select
from .analysis import DEFAULT_CUTS, SIDEBAND_CUTS

__all__ = ['select', 'select_sideband']


def select(indf, cuts=None, **kwargs):
    """Apply nueCC's cut sequence. Defaults ``cuts`` to :data:`DEFAULT_CUTS`."""
    if cuts is None:
        cuts = DEFAULT_CUTS
    return _core_select(indf, cuts=cuts, **kwargs)


def select_sideband(indf, cuts=None, **kwargs):
    """Apply the sideband cut sequence. Defaults ``cuts`` to :data:`SIDEBAND_CUTS`."""
    if cuts is None:
        cuts = SIDEBAND_CUTS
    return _core_select(indf, cuts=cuts, **kwargs)
