"""HNL/pi0's own load_mc()/load_data()/load_mchnl().

``load_mc``/``load_data`` pre-fill :func:`cafpybara.core.io.load_mc`/
``load_data`` with this analysis's own ``rec_key='rec'`` and truth-signal
categorisation. ``load_mchnl`` pre-fills :func:`cafpybara.core.io.load_mevprtl`
(MeVPrtl generator loading) with this analysis's HNL defaults.
"""
from __future__ import annotations

from functools import partial

from ...core.io import (
    load_mc as _core_load_mc, load_data as _core_load_data,
    load_mevprtl as _core_load_mevprtl,
)
from ...core.preprocess import preprocess_mc, preprocess_data
from .analysis import define_signal_pi0, define_signal_hnl, signal_dict_hnl
from .preprocess import preprocess_mchnl

__all__ = ['load_mc', 'load_data', 'load_mchnl']


# ---------------------------------------------------------------------------
# Internal helpers (not exported)
# ---------------------------------------------------------------------------

_define_signal_fn = partial(define_signal_pi0, prefix=('slc', 'truth'))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_mc(
    file: str,
    keys: list | None = None,
    cuts=None,
    max_splits: int | None = None,
    chunk_splits: int = 1,
    add_pi0: bool = False,
    excl_mc_df=None,
    rec_key: str = 'rec',
    preprocess_fn=preprocess_mc,
    define_signal_fn=_define_signal_fn,
):
    """Load an MC HDF5 file. See :func:`cafpybara.core.io.load_mc` for full docs.

    Defaults match this analysis's historical behavior: ``rec_key='rec'``,
    ``preprocess_fn=preprocess_mc`` (base, currently a no-op -- pass e.g.
    ``preprocess_mcbnb`` explicitly for real timing calibration),
    ``define_signal_fn`` stamps this analysis's own ``define_signal_pi0``.
    """
    from ...core.preprocess import add_pi0 as _add_pi0
    add_pi0_fn = _add_pi0 if add_pi0 else None
    return _core_load_mc(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_fn,
        keys=keys, cuts=cuts, max_splits=max_splits, chunk_splits=chunk_splits,
        add_pi0_fn=add_pi0_fn, excl_mc_df=excl_mc_df,
    )


def load_data(
    file: str,
    keys: list | None = None,
    onbeam: bool = True,
    cuts=None,
    rec_key: str = 'rec',
    preprocess_fn=preprocess_data,
    offbeam_signal_value=None,
):
    """Load a data HDF5 file. See :func:`cafpybara.core.io.load_data` for full docs.

    Defaults match this analysis's historical behavior: ``rec_key='rec'``,
    ``preprocess_fn=preprocess_data`` (base, currently a no-op),
    ``offbeam_signal_value=signal_dict_hnl['offbeam']``.
    """
    if not onbeam and offbeam_signal_value is None:
        offbeam_signal_value = signal_dict_hnl['offbeam']
    return _core_load_data(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn,
        keys=keys, onbeam=onbeam, cuts=cuts, offbeam_signal_value=offbeam_signal_value,
    )


def load_mchnl(
    file: str,
    keys: list | None = None,
    mevprtl_key: str = 'mevprtl',
    rec_key: str = 'rec',
    cuts=None,
    preprocess_fn=preprocess_mchnl,
) -> tuple:
    """Load an HNL MeVPrtl MC HDF5 file. See :func:`cafpybara.core.io.load_mevprtl` for full docs.

    Defaults: ``rec_key='rec'``, ``preprocess_fn=preprocess_mchnl`` (real
    MeVPrtl-generator timing calibration -- unlike ``load_mc``/``load_data``,
    which default to the no-op base), signal stamped by ``define_signal_hnl``.
    """
    return _core_load_mevprtl(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_hnl,
        keys=keys, mevprtl_key=mevprtl_key, cuts=cuts,
    )
