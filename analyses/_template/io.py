"""TEMPLATE -- your analysis's own load_mc()/load_data() convenience wrappers.

Pre-fills :func:`cafpybara.core.io.load_mc`/``load_data`` (which have NO
default `rec_key`/`preprocess_fn`/`define_signal_fn` -- those are required,
on purpose, so a new analysis can't accidentally inherit another
topology's values) with this analysis's own real defaults.
"""
from __future__ import annotations

from functools import partial

from ...core.io import load_mc as _core_load_mc, load_data as _core_load_data
from .analysis import define_signal
from .preprocess import preprocess_mc_real, preprocess_data_real

__all__ = ['load_mc', 'load_data']

# TODO: replace with your analysis's real table key (the CAF/ntuple table
# your maker writes the slice-level analysis DataFrame into -- 'rec' for
# hnlpi0, 'nuecc' for nueCC).
REC_KEY = "TODO_SET_ME"

_define_signal_fn = partial(define_signal, prefix=('slc', 'truth'))


def load_mc(
    file: str,
    keys: list | None = None,
    cuts=None,
    max_splits: int | None = None,
    chunk_splits: int = 1,
    rec_key: str = REC_KEY,
    preprocess_fn=preprocess_mc_real,
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
    preprocess_fn=preprocess_data_real,
):
    """Load a data HDF5 file. See :func:`cafpybara.core.io.load_data` for full docs."""
    return _core_load_data(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn,
        keys=keys, onbeam=onbeam, cuts=cuts,
    )
