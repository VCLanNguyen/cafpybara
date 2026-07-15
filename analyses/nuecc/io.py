"""nueCC's own load_mc()/load_data() convenience wrappers.

Pre-fills :func:`cafpybara.core.io.load_mc`/``load_data`` with nueCC's own
``rec_key='nuecc'``, real preprocessing (see ``analyses/nuecc/preprocess.py``
-- not a no-op), and truth-signal categorisation -- matching this village's
historical defaults exactly.
"""

from functools import partial

from ...core.io import load_mc as _core_load_mc, load_data as _core_load_data
from ...core.exclusive import remove_signal_overlap
from .preprocess import preprocess_mc, preprocess_data
from .analysis import define_signal, signal_dict

__all__ = ['load_mc', 'load_data']


# ---------------------------------------------------------------------------
# Internal helpers (not exported)
# ---------------------------------------------------------------------------

_define_signal_fn = partial(define_signal, prefix=('slc', 'truth'))


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
    rec_key: str = 'nuecc',
    preprocess_fn=preprocess_mc,
    define_signal_fn=_define_signal_fn,
):
    """Load an MC HDF5 file. See :func:`cafpybara.core.io.load_mc` for full docs.

    Defaults match nueCC's historical behavior: ``rec_key='nuecc'``,
    ``preprocess_fn=preprocess_mc`` (this village's own real bundler --
    fix_flash_pe_scale/fix_prim_shw_energy/fix_sec_shw_energy/add_phi),
    ``define_signal_fn`` stamps nueCC's own ``define_signal``.
    """
    from ...core.preprocess import add_pi0 as _add_pi0
    add_pi0_fn = _add_pi0 if add_pi0 else None
    return _core_load_mc(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn, define_signal_fn=define_signal_fn,
        keys=keys, cuts=cuts, max_splits=max_splits, chunk_splits=chunk_splits,
        add_pi0_fn=add_pi0_fn, excl_mc_df=excl_mc_df,
        remove_signal_overlap_fn=remove_signal_overlap if excl_mc_df is not None else None,
    )


def load_data(
    file: str,
    keys: list | None = None,
    onbeam: bool = True,
    cuts=None,
    rec_key: str = 'nuecc',
    preprocess_fn=preprocess_data,
    offbeam_signal_value=None,
):
    """Load a data HDF5 file. See :func:`cafpybara.core.io.load_data` for full docs.

    Defaults match nueCC's historical behavior: ``rec_key='nuecc'``,
    ``preprocess_fn=preprocess_data`` (this village's own real bundler --
    fix_flash_time/fix_prim_shw_energy/fix_sec_shw_energy/add_phi),
    ``offbeam_signal_value=signal_dict['offbeam']``.
    """
    if not onbeam and offbeam_signal_value is None:
        offbeam_signal_value = signal_dict['offbeam']
    return _core_load_data(
        file, rec_key=rec_key, preprocess_fn=preprocess_fn,
        keys=keys, onbeam=onbeam, cuts=cuts, offbeam_signal_value=offbeam_signal_value,
    )
