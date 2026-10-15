"""TEMPLATE -- your analysis's own load_mc()/load_data()/load_mchnl() convenience wrappers.

Pre-fills :func:`cafpybara.core.io.load_mc`/``load_data`` (which have NO
default `rec_key`/`preprocess_fn`/`define_signal_fn` -- those are required,
on purpose, so a new analysis can't accidentally inherit another
topology's values) with this analysis's own defaults.
"""
from __future__ import annotations

from functools import partial

from ...core.io import (
    load_mc as _core_load_mc, load_data as _core_load_data,
    load_mevprtl as _core_load_mevprtl,
)
from .analysis import define_signal, define_signal_hnl
from .preprocess import preprocess_mc, preprocess_data, preprocess_mchnl

__all__ = ['load_mc', 'load_data', 'load_mchnl']

# TODO: set your slc-level table key (e.g. 'rec', 'nuecc').
REC_KEY = "TODO_SET_ME"

_define_signal_fn = partial(define_signal, prefix=('slc', 'truth'))


def load_mc(
    file: str,
    keys: list | None = None,
    cuts=None,
    max_splits: int | None = None,
    chunk_splits: int = 1,
    rec_key: str = REC_KEY,
    preprocess_fn=preprocess_mc,
    define_signal_fn=_define_signal_fn,
):
    """Load an MC HDF5 file. See :func:`cafpybara.core.io.load_mc` for full docs."""
    return _core_load_mc(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_fn,
        keys=keys, cuts=cuts, max_splits=max_splits, chunk_splits=chunk_splits,
    )


def load_data(
    file: str,
    keys: list | None = None,
    onbeam: bool = True,
    cuts=None,
    rec_key: str = REC_KEY,
    preprocess_fn=preprocess_data,
):
    """Load a data HDF5 file. See :func:`cafpybara.core.io.load_data` for full docs."""
    return _core_load_data(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn,
        keys=keys, onbeam=onbeam, cuts=cuts,
    )


def load_mchnl(
    file: str,
    keys: list | None = None,
    mevprtl_key: str = 'mevprtl',
    cuts=None,
    rec_key: str = REC_KEY,
    preprocess_fn=preprocess_mchnl,
    define_signal_fn=define_signal_hnl,
):
    """Optional -- load a MeVPrtl (e.g. HNL) MC HDF5 file. See
    :func:`cafpybara.core.io.load_mevprtl` for full docs.

    TODO: delete if your analysis has no MeVPrtl sample.
    """
    return _core_load_mevprtl(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_fn,
        keys=keys, mevprtl_key=mevprtl_key, cuts=cuts,
    )
