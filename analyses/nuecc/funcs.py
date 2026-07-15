"""nueCC's own get_total_cov() convenience wrapper.

Resolves nueCC's ``select_region`` naming ('signal'/'control'/'all') to its
own detvar file paths, and its own in-time-cosmic file/key/offbeam-value --
matching this village's historical defaults exactly, including the
``cuts=None`` -> ``DEFAULT_CUTS`` fallback that nueCC's own example
notebooks currently rely on (they don't always pass ``cuts=`` explicitly).
"""

from ...core.funcs import get_total_cov as _core_get_total_cov
from . import config
from .analysis import DEFAULT_CUTS, define_signal, signal_dict
from .preprocess import preprocess_mc

__all__ = ['get_total_cov']


# ---------------------------------------------------------------------------
# Internal helpers (not exported)
# ---------------------------------------------------------------------------

_select_region_map = {
    "signal":  config.DETVAR_DICT_SIGNAL,
    "control": config.DETVAR_DICT_CONTROL,
    "all":     config.DETVAR_DICT_FILES,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_total_cov(reco_df, reco_var, bins, mcbnb_pot,
                  cuts=None, select_region: str = "signal",
                  detvar_dict=None, detvar_files=None,
                  intime_file=None, intime_key=None, offbeam_value=None,
                  intime_preprocess_fn=None,
                  define_signal_fn=None,
                  uncertainty_keys=None,
                  **kwargs):
    """Get the total event-rate (and optional xsec) covariance for nueCC.

    See :func:`cafpybara.core.funcs.get_total_cov` for the full parameter
    list. Differences from the core function:

    - ``cuts=None`` defaults to :data:`~cafpybara.analyses.nuecc.analysis.DEFAULT_CUTS`.
    - ``select_region`` ('signal'/'control'/'all', default 'signal') resolves
      to nueCC's own detvar file(s) via ``config.DETVAR_DICT_SIGNAL``/
      ``_CONTROL``/``_FILES`` when ``detvar_dict``/``detvar_files`` aren't
      given explicitly.
    - ``intime_file``/``intime_key``/``offbeam_value`` default to nueCC's own
      ``config.INTIME_FILE``/``'nuecc'``/``signal_dict['offbeam']`` -- so
      ``'cosmic'`` is included by default here (unlike core), matching
      nueCC's historical default ``uncertainty_keys``.
    - ``define_signal_fn`` defaults to nueCC's own ``define_signal``.
    """
    if cuts is None:
        cuts = DEFAULT_CUTS
    if select_region not in _select_region_map:
        raise ValueError(f"select_region must be one of {list(_select_region_map)}, got '{select_region}'")
    if detvar_dict is None and detvar_files is None:
        detvar_files = _select_region_map[select_region]
    if intime_file is None:
        intime_file = config.INTIME_FILE
    if intime_key is None:
        intime_key = 'nuecc'
    if offbeam_value is None:
        offbeam_value = signal_dict['offbeam']
    if intime_preprocess_fn is None:
        intime_preprocess_fn = preprocess_mc
    if define_signal_fn is None:
        define_signal_fn = define_signal
    if uncertainty_keys is None:
        uncertainty_keys = {'rate', 'detv', 'norm', 'cosmic'}

    return _core_get_total_cov(
        reco_df, reco_var, bins, mcbnb_pot,
        cuts=cuts, detvar_dict=detvar_dict, detvar_files=detvar_files,
        intime_file=intime_file, intime_key=intime_key, offbeam_value=offbeam_value,
        intime_preprocess_fn=intime_preprocess_fn,
        define_signal_fn=define_signal_fn, uncertainty_keys=uncertainty_keys,
        **kwargs,
    )
