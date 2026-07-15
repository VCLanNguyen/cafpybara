"""HNL/pi0's own plot_var()/plot_mc_data()/plot_mc_hnl_data() convenience wrappers.

Pre-fills :func:`cafpybara.core.plotting.plot_var` (and anything that calls
it internally) with this village's own default category dict
(:data:`~cafpybara.analyses.hnlpi0.analysis.background_categories_hnl` -- the
MC-stack view that excludes the HNL-only 'hnl'/'hnlcosmic' entries).
"""

from ...core import plotting as _core_plotting
from ...core.physics import pdg_categories as _pdg_categories, mode_categories as _mode_categories
from .analysis import background_categories_hnl, signal_dict_hnl

__all__ = [
    'annotate_sbnd', 'plot_var', 'plot_var_pdg', 'data_plot_overlay',
    'plot_mc_data', 'plot_mc_hnl_data', 'plot_mc_hnl',
    'plot_detvar', 'plot_syst_category_breakdown', 'plot_syst_breakdown',
]

annotate_sbnd = _core_plotting.annotate_sbnd
data_plot_overlay = _core_plotting.data_plot_overlay
plot_detvar = _core_plotting.plot_detvar
plot_syst_category_breakdown = _core_plotting.plot_syst_category_breakdown
plot_syst_breakdown = _core_plotting.plot_syst_breakdown


def _inject_defaults(kwargs):
    kwargs.setdefault('categories', None)
    if kwargs['categories'] is None and not kwargs.get('pdg') and not kwargs.get('mode'):
        kwargs['categories'] = background_categories_hnl
    kwargs.setdefault('pdg_categories', _pdg_categories)
    kwargs.setdefault('mode_categories', _mode_categories)
    kwargs.setdefault('signal_dict', signal_dict_hnl)
    return kwargs


def plot_var(df, var, bins, ax=None, config=None, **kwargs):
    """Stacked histogram, defaulting to :data:`background_categories_hnl`.

    See :func:`cafpybara.core.plotting.plot_var` for the full parameter list.
    """
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_var(df, var, bins, ax=ax, config=config, **kwargs)


def plot_var_pdg(**args):
    """Backward-compatible wrapper: calls :func:`plot_var` with ``pdg=True``."""
    return plot_var(pdg=True, **args)


def plot_mc_data(mc_df, data_df, var, bins, **kwargs):
    """Combined MC stack + data overlay. See :func:`cafpybara.core.plotting.plot_mc_data`."""
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_mc_data(mc_df, data_df, var, bins, **kwargs)


def plot_mc_hnl_data(mc_df, hnl_df, data_df, var, bins, **kwargs):
    """MC stack + HNL step overlay + data. See :func:`cafpybara.core.plotting.plot_mc_hnl_data`."""
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_mc_hnl_data(mc_df, hnl_df, data_df, var, bins, **kwargs)


def plot_mc_hnl(mc_df, hnl_df, var, bins, **kwargs):
    """MC stack + HNL step overlay, no data. See :func:`cafpybara.core.plotting.plot_mc_hnl`."""
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_mc_hnl(mc_df, hnl_df, var, bins, **kwargs)
