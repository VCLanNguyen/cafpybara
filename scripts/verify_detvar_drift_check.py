"""Standalone verification for the detvar cuts_signature drift check (Part B).

Uses small synthetic data -- no real ntuples, no real detvar_*.df files --
so this can run anywhere with pandas/numpy/cafpybara importable (e.g. EAF),
without needing access to nueCC's raw detvar inputs.

Run with:
    python scripts/verify_detvar_drift_check.py

Exits non-zero (with a clear message) on the first failed check.
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd

from cafpybara.core.classes import CutSpec
from cafpybara.core.syst import get_detvar_systs
from cafpybara.core.detvar.store import DetVarFile, write_detvar_store, load_detvar_dict

FAILURES = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        FAILURES.append(label)


def expect_raises(label, fn, match=None):
    try:
        fn()
    except ValueError as e:
        if match is not None and match not in str(e):
            check(label, False)
            print(f"       raised, but message didn't contain {match!r}: {e}")
        else:
            check(label, True)
        return
    check(label, False)
    print(f"       expected a ValueError, nothing was raised")


def expect_ok(label, fn):
    try:
        fn()
    except ValueError as e:
        check(label, False)
        print(f"       unexpected raise: {e}")
        return
    check(label, True)


# ---------------------------------------------------------------------------
# Layer 1: unit-test the drift-check logic directly, no HDF5 round-trip.
# Synthetic CV/DV already "pre-selected" at fv in [0, 8) -- simulates a
# store built with fiducial_volume: 0 < fv < 8.
# ---------------------------------------------------------------------------

def make_flat_df(n, fv_lo, fv_hi, seed):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        'e':  rng.uniform(0.0, 5.0, n),
        'fv': rng.uniform(fv_lo, fv_hi, n),
    })


N = 2000
cv_df = make_flat_df(N, 0.0, 8.0, seed=1)
dv_df = make_flat_df(N, 0.0, 8.0, seed=2)
bins = np.linspace(0.0, 5.0, 6)

base_dict = {
    'test_group': {
        'dv_df': dv_df,
        'cv_df': cv_df,
        'pot': 1e18,
        'cuts_signature': ['fiducial_volume'],
        'stage': None,
    }
}

fv_same   = CutSpec('fiducial_volume', variable=('fv',), min=0, max=8)   # matches what "built" the store
fv_drift  = CutSpec('fiducial_volume', variable=('fv',), min=0, max=5)   # same name, narrower bound = drift
other_cut = CutSpec('other_cut',       variable=('e',),  min=0, max=5)
extra_cut = CutSpec('extra_trk_cut',   variable=('e',),  min=0, max=3)

print("--- Layer 1: unit-test get_detvar_systs()'s drift check ---")

expect_ok(
    "(a) live cuts match the stamp exactly -> no error",
    lambda: get_detvar_systs(base_dict, 'e', bins, cuts=[fv_same]),
)

expect_raises(
    "(b) same cut name, drifted definition -> raises drift error",
    lambda: get_detvar_systs(base_dict, 'e', bins, cuts=[fv_drift]),
    match="drifted",
)

expect_raises(
    "(c) live cuts missing the stamped cut entirely -> raises missing-cut error",
    lambda: get_detvar_systs(base_dict, 'e', bins, cuts=[other_cut]),
    match="missing",
)

expect_ok(
    "(d) live cuts legitimately extend the stamp (narrowing case) -> no error",
    lambda: get_detvar_systs(base_dict, 'e', bins, cuts=[fv_same, extra_cut]),
)

no_stamp_dict = {
    'test_group': {**base_dict['test_group'], 'cuts_signature': None},
}
expect_ok(
    "(e) no stamp present -> skipped silently, no error",
    lambda: get_detvar_systs(no_stamp_dict, 'e', bins, cuts=[fv_drift]),
)


# ---------------------------------------------------------------------------
# Layer 2: round-trip cuts_signature/stage through a real HDF5 store via
# write_detvar_store/load_detvar_dict, confirming the stamp survives storage.
# ---------------------------------------------------------------------------

print("\n--- Layer 2: HDF5 round-trip for cuts_signature/stage ---")

import tempfile, os

def make_matched_pair(n, seed_cv, seed_dv):
    rng = np.random.default_rng(0)
    shared = pd.DataFrame({
        'run': 1, 'subrun': 1, 'evt': np.arange(n),
        'E': np.round(rng.uniform(0.1, 2.0, n), 6),
    })

    def _lite(seed):
        df = shared.copy()
        df['pot'] = 1e18 / n
        df['__ntuple'] = 0
        df['entry'] = np.arange(n)
        df['file_idx'] = 0
        return df.set_index(['run', 'subrun', 'evt', 'E'])

    def _slc(seed, fv_lo, fv_hi):
        r = np.random.default_rng(seed)
        df = pd.DataFrame({
            'e':  r.uniform(0.0, 5.0, n),
            'fv': r.uniform(fv_lo, fv_hi, n),
            '__ntuple': 0,
            'entry': np.arange(n),
            'file_idx': 0,
        })
        return df.set_index(['__ntuple', 'entry', 'file_idx'])

    cv = DetVarFile(lite_df=_lite(seed_cv), slc_df=_slc(seed_cv, 0.0, 8.0))
    dv = DetVarFile(lite_df=_lite(seed_dv), slc_df=_slc(seed_dv, 0.0, 8.0))
    return cv, dv


cv_file, dv_file = make_matched_pair(500, seed_cv=10, seed_dv=11)

with tempfile.TemporaryDirectory() as tmpdir:
    out_path = os.path.join(tmpdir, 'test_detvars.h5')
    write_detvar_store(
        out_path,
        cv_dict={'cv_0': cv_file},
        dv_dict={'test_group': dv_file},
        cv_map={'test_group': 'cv_0'},
        cuts_signature=['fiducial_volume'],
        stage=None,
    )
    loaded = load_detvar_dict(out_path)

    check(
        "(f) cuts_signature survives the HDF5 round-trip",
        loaded.get('test_group', {}).get('cuts_signature') == ['fiducial_volume'],
    )
    check(
        "(g) stage survives the HDF5 round-trip as None",
        loaded.get('test_group', {}).get('stage') is None,
    )

    # And confirm get_detvar_systs works end-to-end against the loaded store.
    expect_ok(
        "(h) loaded store + matching live cuts -> no error",
        lambda: get_detvar_systs(loaded, 'e', bins, cuts=[fv_same]),
    )
    expect_raises(
        "(i) loaded store + drifted live cuts -> raises drift error",
        lambda: get_detvar_systs(loaded, 'e', bins, cuts=[fv_drift]),
        match="drifted",
    )

    # Also verify an unstamped (mode='w', no cuts_signature) store round-trips
    # cleanly as None, matching legacy/foreign stores like Lynn's.
    out_path2 = os.path.join(tmpdir, 'test_detvars_nostamp.h5')
    write_detvar_store(
        out_path2,
        cv_dict={'cv_0': cv_file},
        dv_dict={'test_group': dv_file},
        cv_map={'test_group': 'cv_0'},
    )
    loaded2 = load_detvar_dict(out_path2)
    check(
        "(j) store written with no cuts_signature loads back as None",
        loaded2.get('test_group', {}).get('cuts_signature') is None,
    )


print()
if FAILURES:
    print(f"{len(FAILURES)} check(s) FAILED:")
    for f in FAILURES:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All checks passed.")
