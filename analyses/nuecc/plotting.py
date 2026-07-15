"""nueCC's own plot_var()/plot_mc_data() convenience wrappers.

Pre-fills :func:`cafpybara.core.plotting.plot_var` (and anything that calls
it internally, e.g. ``plot_mc_data``) with nueCC's own default category
dicts -- matching this village's historical default (stack by
``signal_categories`` unless ``pdg=``/``mode=``/``categories=`` say
otherwise).

Everything else in :mod:`cafpybara.core.plotting` (``data_plot_overlay``,
``plot_detvar``, ``plot_syst_category_breakdown``, ``plot_syst_breakdown``,
...) takes no topology default internally, so it's re-exported unchanged.
"""

from ...core import plotting as _core_plotting
from ...core.physics import pdg_categories as _pdg_categories, mode_categories as _mode_categories
from .analysis import signal_categories, signal_dict

__all__ = [
    'annotate_sbnd', 'plot_var', 'plot_var_pdg', 'data_plot_overlay',
    'plot_mc_data', 'plot_detvar', 'plot_syst_category_breakdown', 'plot_syst_breakdown',
]

annotate_sbnd = _core_plotting.annotate_sbnd
data_plot_overlay = _core_plotting.data_plot_overlay
plot_detvar = _core_plotting.plot_detvar
plot_syst_category_breakdown = _core_plotting.plot_syst_category_breakdown
plot_syst_breakdown = _core_plotting.plot_syst_breakdown


# ---------------------------------------------------------------------------
# Internal helpers (not exported)
# ---------------------------------------------------------------------------

_DEFAULT_PDG_COL = 'pfp_shw_truth_p_pdg'


def _inject_defaults(kwargs):
    kwargs.setdefault('categories', None)
    if kwargs['categories'] is None and not kwargs.get('pdg') and not kwargs.get('mode'):
        kwargs['categories'] = signal_categories
    kwargs.setdefault('pdg_categories', _pdg_categories)
    kwargs.setdefault('mode_categories', _mode_categories)
    kwargs.setdefault('signal_dict', signal_dict)
    kwargs.setdefault('pdg_col', _DEFAULT_PDG_COL)
    return kwargs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plot_var(df, var, bins, ax=None, config=None, **kwargs):
    """Stacked histogram, defaulting to nueCC's own ``signal_categories``.

    See :func:`cafpybara.core.plotting.plot_var` for the full parameter list.
    """
    if config is not None:
        from dataclasses import fields as _dc_fields
        _cfg = {f.name: getattr(config, f.name) for f in _dc_fields(config)}
        for k in ('categories', 'pdg_categories', 'mode_categories', 'signal_dict', 'pdg_col'):
            if _cfg.get(k) is not None:
                kwargs.setdefault(k, _cfg[k])
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_var(df, var, bins, ax=ax, config=config, **kwargs)


def plot_var_pdg(**args):
    """Backward-compatible wrapper: calls :func:`plot_var` with ``pdg=True``."""
    return plot_var(pdg=True, **args)


def plot_mc_data(mc_df, data_df, var, bins, **kwargs):
    """Combined MC stack + data overlay, defaulting to nueCC's own categories.

    See :func:`cafpybara.core.plotting.plot_mc_data` for the full parameter list.
    """
    config = kwargs.pop('config', None)
    if config is not None:
        from dataclasses import fields as _dc_fields
        _cfg = {f.name: getattr(config, f.name) for f in _dc_fields(config)}
        for k in ('categories', 'pdg_categories', 'mode_categories', 'signal_dict', 'pdg_col'):
            if _cfg.get(k) is not None:
                kwargs.setdefault(k, _cfg[k])
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_mc_data(mc_df, data_df, var, bins, config=config, **kwargs)
