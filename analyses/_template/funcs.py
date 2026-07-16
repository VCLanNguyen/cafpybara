"""TEMPLATE -- your analysis's own SystematicsInput factory.

Do NOT define your own `get_total_cov` here. `core.funcs.get_total_cov` is
the single real implementation for every analysis -- this file's only job
is `systs_input()`, a factory that fully resolves every real default into
a concrete value before anything reaches `core`. This exact rule is the
direct outcome of a real, live bug found in this project (nueCC's plotted
error bands silently missing an uncertainty source that its own drill-down
cells had, because two different code paths independently -- and
differently -- filled in `get_total_cov`'s defaults). See
`examples/build_a_new_analysis.ipynb`'s systematics section for the full
story; don't reintroduce a `get_total_cov` override here even if it looks
like a convenient shortcut.
"""

from ...core.classes import SystematicsInput
from . import config
from .analysis import DEFAULT_CUTS, define_signal
from .preprocess import preprocess_mc_real

__all__ = ['systs_input']


def systs_input(mcbnb_pot, *, cuts=None, uncertainty_keys=None, **kwargs):
    """Build a fully-resolved SystematicsInput for this analysis.

    Pass the result straight to :func:`~cafpybara.core.funcs.get_total_cov`
    via ``**systs_input(...).to_kwargs()``, or to
    :class:`~cafpybara.core.classes.PlottingConfig`'s ``systs=`` argument --
    both resolve identically since both consume the same already-resolved
    `SystematicsInput`, which is the whole point of routing everything
    through this one factory.

    TODO: adjust which fields get a real default here to match your
    topology. `cuts=None -> DEFAULT_CUTS` mirrors nueCC's convention (only
    sensible if your topology, like nueCC, has one single obviously-correct
    default cut list); if it has several valid modes with no single
    default -- like hnlpi0 -- make `cuts` a required argument instead (drop
    the `= None` and the `if cuts is None` block below), the same call
    hnlpi0.funcs.systs_input makes.
    """
    if cuts is None:
        cuts = DEFAULT_CUTS

    detvar_dict = kwargs.pop('detvar_dict', None)
    detvar_files = kwargs.pop('detvar_files', None)
    if detvar_dict is None and detvar_files is None:
        # TODO: this is where your topology's real detvar file(s) get
        # filled in by default -- see config.DETVAR_DICT_FILES above.
        detvar_files = config.DETVAR_DICT_FILES

    kwargs.setdefault('define_signal_fn', define_signal)

    # TODO: if your topology has a real in-time-cosmic sample, default
    # intime_file/intime_key/offbeam_value/intime_preprocess_fn here (see
    # nuecc.funcs.systs_input for a real, working example) and let
    # 'cosmic' into the default uncertainty_keys below. If it doesn't,
    # leave 'cosmic' out of the default and raise a clear error if it's
    # explicitly requested -- see hnlpi0.funcs.systs_input's ValueError.
    if uncertainty_keys is not None and 'cosmic' in set(uncertainty_keys):
        raise ValueError(
            "TEMPLATE: 'cosmic' was requested, but no in-time-cosmic sample "
            "has been configured for this analysis yet. Either configure "
            "one (see the TODO above) or drop 'cosmic' from uncertainty_keys."
        )
    if uncertainty_keys is None:
        uncertainty_keys = {'rate', 'detv', 'norm'}

    return SystematicsInput(
        mcbnb_pot=mcbnb_pot, cuts=cuts, detvar_dict=detvar_dict, detvar_files=detvar_files,
        uncertainty_keys=uncertainty_keys, **kwargs,
    )
