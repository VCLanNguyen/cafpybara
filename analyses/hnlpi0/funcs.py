"""HNL/pi0's own SystematicsInput factory.

Unlike nueCC, there is only one detvar region ('all' -- no signal/control
split exists for this topology) and no in-time-cosmic sample exists at all,
so 'cosmic' is NOT included by default and raises a clear error if
explicitly requested. `cuts` has no default here either -- PI0_CUT_LISTS has
multiple valid modes, so the caller must always pass one explicitly (matching
this village's actual notebook usage today).

``get_total_cov`` is intentionally NOT defined here, for the same reason as
nueCC's equivalent module -- ``core.funcs.get_total_cov`` is the single real
implementation, and this village's one real call site
(``hnl_analysis_v6.ipynb``) already goes through ``.to_kwargs()``.
``hnlpi0.get_total_cov`` resolves via this package's ``__init__.py``
re-exporting ``core.funcs.get_total_cov`` directly.
"""

from . import config
from ...core.classes import SystematicsInput

__all__ = ['systs_input']


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def systs_input(mchnl_pot, cuts, **kwargs):
    """Build a fully-resolved SystematicsInput for HNL/pi0.

    Differences from a bare :class:`~cafpybara.core.classes.SystematicsInput`:

    - ``cuts`` is required (positional) -- no default, since
      :data:`~cafpybara.analyses.hnlpi0.analysis.PI0_CUT_LISTS` has multiple
      valid modes with no single obviously-correct choice.
    - ``detvar_dict``/``detvar_files`` default to
      ``config.HNL_DETVAR_DICT_FILES`` when neither is given explicitly.
    - ``'cosmic'`` raises if explicitly requested in ``uncertainty_keys`` --
      no in-time-cosmic sample exists for this topology (see ``config.py``
      docstring).
    """
    uncertainty_keys = kwargs.get('uncertainty_keys')
    if uncertainty_keys is not None and 'cosmic' in set(uncertainty_keys):
        raise ValueError(
            "hnlpi0.systs_input: 'cosmic' was requested, but no in-time-cosmic "
            "sample exists for this topology yet (see cafpybara.analyses.hnlpi0."
            "config's docstring). Drop 'cosmic' from uncertainty_keys."
        )
    detvar_dict = kwargs.pop('detvar_dict', None)
    detvar_files = kwargs.pop('detvar_files', None)
    if detvar_dict is None and detvar_files is None:
        detvar_files = config.HNL_DETVAR_DICT_FILES

    return SystematicsInput(
        mcbnb_pot=mchnl_pot, cuts=cuts, detvar_dict=detvar_dict, detvar_files=detvar_files,
        **kwargs,
    )
