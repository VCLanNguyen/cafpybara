"""HNL/pi0's own get_total_cov() convenience wrapper.

Unlike nueCC, there is only one detvar region ('all' -- no signal/control
split exists for this topology) and no in-time-cosmic sample exists at all,
so 'cosmic' is NOT included by default and raises a clear error if
explicitly requested. `cuts` has no default here either -- PI0_CUT_LISTS has
multiple valid modes, so the caller must always pass one explicitly (matching
this village's actual notebook usage today).
"""

from ...core.funcs import get_total_cov as _core_get_total_cov
from . import config

__all__ = ['get_total_cov']


def get_total_cov(reco_df, reco_var, bins, mcbnb_pot,
                  cuts, detvar_dict=None, detvar_files=None,
                  uncertainty_keys=None,
                  **kwargs):
    """Get the total event-rate (and optional xsec) covariance for HNL/pi0.

    See :func:`cafpybara.core.funcs.get_total_cov` for the full parameter
    list. Differences from the core function:

    - ``cuts`` is required (positional) -- no default, since
      :data:`~cafpybara.analyses.hnlpi0.analysis.PI0_CUT_LISTS` has multiple
      valid modes with no single obviously-correct choice.
    - ``detvar_dict``/``detvar_files`` default to
      ``config.HNL_DETVAR_DICT_FILES`` when 'detv' is requested and neither
      is given explicitly.
    - ``'cosmic'`` is not included by default (matches core) and raises if
      explicitly requested -- no in-time-cosmic sample exists for this
      topology (see ``config.py`` docstring).
    """
    if uncertainty_keys is not None and 'cosmic' in set(uncertainty_keys):
        raise ValueError(
            "hnlpi0.get_total_cov: 'cosmic' was requested, but no in-time-cosmic "
            "sample exists for this topology yet (see cafpybara.analyses.hnlpi0."
            "config's docstring). Drop 'cosmic' from uncertainty_keys."
        )
    if detvar_dict is None and detvar_files is None:
        detvar_files = config.HNL_DETVAR_DICT_FILES

    return _core_get_total_cov(
        reco_df, reco_var, bins, mcbnb_pot,
        cuts=cuts, detvar_dict=detvar_dict, detvar_files=detvar_files,
        uncertainty_keys=uncertainty_keys,
        **kwargs,
    )
