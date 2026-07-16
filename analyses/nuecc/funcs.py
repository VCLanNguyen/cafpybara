"""nueCC's own SystematicsInput factory.

Resolves nueCC's ``select_region`` naming ('signal'/'control'/'all') to its
own detvar file paths, and its own in-time-cosmic file/key/offbeam-value --
matching this analysis's historical defaults exactly, including the
``cuts=None`` -> ``DEFAULT_CUTS`` fallback that nueCC's own example
notebooks currently rely on (they don't always pass ``cuts=`` explicitly).

``get_total_cov`` is intentionally NOT defined here -- ``core.funcs
.get_total_cov`` is the single real implementation, and every real call site
(both the direct notebook drill-down calls and core.plotting's
``systs=SystematicsInput(...)`` handling) already goes through
``.to_kwargs()``. Keeping a second, analysis-local wrapper function around it
is exactly the kind of duplicate-code-path that caused this module's
defaults to silently diverge from core.plotting's before (see the
architecture-rethink notes in claude_memory.md). ``nuecc.get_total_cov``
resolves via this package's ``__init__.py`` re-exporting
``core.funcs.get_total_cov`` directly -- unshadowed now that this file no
longer defines its own.
"""

from . import config
from .analysis import DEFAULT_CUTS, define_signal, signal_dict
from .preprocess import preprocess_mc
from ...core.classes import SystematicsInput

__all__ = ['systs_input']


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

def systs_input(mcbnb_pot, *, cuts=None, select_region: str = "signal",
                 uncertainty_keys=None, **kwargs):
    """Build a fully-resolved SystematicsInput for nueCC.

    The single place nueCC's real defaults get filled in -- pass the result
    straight to :func:`~cafpybara.core.funcs.get_total_cov` via
    ``**systs_input(...).to_kwargs()``, or to
    :class:`~cafpybara.core.classes.PlottingConfig`'s ``systs=`` argument.
    Both paths resolve identically since both consume the same already-fully
    -resolved :class:`~cafpybara.core.classes.SystematicsInput`.

    Differences from a bare :class:`~cafpybara.core.classes.SystematicsInput`:

    - ``cuts=None`` defaults to :data:`~cafpybara.analyses.nuecc.analysis.DEFAULT_CUTS`.
    - ``select_region`` ('signal'/'control'/'all', default 'signal') resolves
      to nueCC's own detvar file(s) via ``config.DETVAR_DICT_SIGNAL``/
      ``_CONTROL``/``_FILES`` when ``detvar_dict``/``detvar_files`` aren't
      given explicitly.
    - ``intime_file``/``intime_key``/``offbeam_value`` default to nueCC's own
      ``config.INTIME_FILE``/``'nuecc'``/``signal_dict['offbeam']`` -- so
      ``'cosmic'`` is included by default here (unlike core), matching
      nueCC's historical default ``uncertainty_keys``.
    - ``intime_preprocess_fn`` defaults to nueCC's own real ``preprocess_mc``
      (imported above) -- NOT core's generic no-op of the same name.
    - ``define_signal_fn`` defaults to nueCC's own ``define_signal``.
    """
    if cuts is None:
        cuts = DEFAULT_CUTS
    if select_region not in _select_region_map:
        raise ValueError(f"select_region must be one of {list(_select_region_map)}, got '{select_region}'")
    detvar_dict = kwargs.pop('detvar_dict', None)
    detvar_files = kwargs.pop('detvar_files', None)
    if detvar_dict is None and detvar_files is None:
        detvar_files = _select_region_map[select_region]
    kwargs.setdefault('intime_file', config.INTIME_FILE)
    kwargs.setdefault('intime_key', 'nuecc')
    kwargs.setdefault('offbeam_value', signal_dict['offbeam'])
    kwargs.setdefault('intime_preprocess_fn', preprocess_mc)
    kwargs.setdefault('define_signal_fn', define_signal)
    if uncertainty_keys is None:
        uncertainty_keys = {'rate', 'detv', 'norm', 'cosmic'}

    return SystematicsInput(
        mcbnb_pot=mcbnb_pot, cuts=cuts, detvar_dict=detvar_dict, detvar_files=detvar_files,
        uncertainty_keys=uncertainty_keys, **kwargs,
    )
