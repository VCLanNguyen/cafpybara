"""TEMPLATE -- your analysis's own plot_var()/plot_mc_data() convenience wrappers.

Pre-fills :func:`cafpybara.core.plotting.plot_var` (and anything that calls
it internally, e.g. `plot_mc_data`) with this analysis's own default
category dict -- `core.plot_var` itself has NO category default at all and
raises a clear error if one can't be resolved, on purpose.
"""

from ...core import plotting as _core_plotting
from .analysis import signal_categories, signal_dict

__all__ = ['plot_var', 'plot_mc_data']


def _inject_defaults(kwargs):
    kwargs.setdefault('categories', None)
    if kwargs['categories'] is None and not kwargs.get('pdg') and not kwargs.get('mode'):
        kwargs['categories'] = signal_categories
    kwargs.setdefault('signal_dict', signal_dict)
    # TODO: pdg_col varies per variable -- pass explicitly per call, not here.
    return kwargs


def plot_var(df, var, bins, ax=None, config=None, **kwargs):
    """Stacked histogram, defaulting to this analysis's own `signal_categories`.

    See :func:`cafpybara.core.plotting.plot_var` for the full parameter list.
    """
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_var(df, var, bins, ax=ax, config=config, **kwargs)


def plot_mc_data(mc_df, data_df, var, bins, **kwargs):
    """Combined MC stack + data overlay, defaulting to this analysis's own categories.

    See :func:`cafpybara.core.plotting.plot_mc_data` for the full parameter list.
    """
    kwargs = _inject_defaults(kwargs)
    return _core_plotting.plot_mc_data(mc_df, data_df, var, bins, **kwargs)
