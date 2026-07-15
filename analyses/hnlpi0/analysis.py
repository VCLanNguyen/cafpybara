"""HNL/pi0 analysis configuration -- signal categories, cut-list modes, and
truth categorisation.

Shared/generic pieces (physical constants, generic_categories, pdg_categories,
mode_categories, category_dict_signal/control) live in
:mod:`cafpybara.core.physics` -- this file holds only what's genuinely
HNL/pi0-specific.

Unlike nueCC, there is no single obviously-correct default cut list --
:data:`PI0_CUT_LISTS` holds several valid modes (``'1shw'``, ``'2shw'``,
``'either_shw'``, ...). Pick one explicitly via :func:`select_by_mode_pi0`
or ``cuts=PI0_CUT_LISTS[mode]``.
"""

import numpy as np
import pandas as pd
from makedf.util import InFV, InAV

from ...core.classes import CutSpec
from ...core.selection import select, union_cut

__all__ = [
    'signal_categories_hnl', 'signal_dict_hnl', 'background_categories_hnl',
    'HNL_DISPLAY_SCALE', 'hnl_categories_for_mass',
    'PI0_PRESEL_CUTS', 'PI0_CUTS_COMMON', 'PI0_CUTS_1SHW', 'PI0_CUTS_2SHW',
    'PI0_CUTS_1SHW_ANGLE', 'PI0_CUTS_2SHW_ANGLE', 'PI0_CUTS_EITHER_SHW',
    'PI0_CUTS_EITHER_ANGLE', 'PI0_CUT_LISTS', 'select_by_mode_pi0',
    'define_signal_pi0', 'define_signal_hnl',
]


# ---------------------------------------------------------------------------
# Signal/background category definitions
# ---------------------------------------------------------------------------

# HNL analysis: signal == 0 is the desired topology (HNL, including HNL cosmic).
# Colors are the Sheffield palette used by the original HNL plotting code.
signal_categories_hnl = {
    "hnl":          {"value": 0,  "label": "HNL",                     "color": "#E7004C"},  # Coral
    "CCpi0":        {"value": 1,  "label": r"CC$\nu$$\pi^0$",         "color": "#00CE7C"},  # MintGreen
    "NCpi0":        {"value": 2,  "label": r"NC$\nu$$\pi^0$",         "color": "#FF6371"},  # Flamingo
    "othernumuCC":  {"value": 3,  "label": r"Other CC $\nu_\mu$",     "color": "#005A8F"},  # Teal
    "otherNC":      {"value": 4,  "label": r"Other NC $\nu$",         "color": "#DAA8E2"},  # Lavender
    "CCnue":        {"value": 5,  "label": r"CC $\nu_e$",             "color": "#00BBCC"},  # Aqua
    "nonFV":        {"value": 6,  "label": r"Non-FV $\nu$",           "color": "#FF9664"},  # Peach
    "dirt":         {"value": 7,  "label": r"Dirt $\nu$",             "color": "#8B6969"},  # RosyBrown4
    "cosmic":       {"value": 8,  "label": "Cosmic",                  "color": "#708090"},  # SlateGray
    "offbeam":      {"value": 9,  "label": "Offbeam",                 "color": "#D0D2D4"},  # LightGray
    "hnlcosmic":    {"value": 10, "label": "HNL Cosmic",              "color": "#131E29"},  # MidnightBlack
}
signal_dict_hnl = {k: v["value"] for k, v in signal_categories_hnl.items()}

# Background-only view of signal_categories_hnl, for the MC stack in plot_mc_hnl_data/
# plot_mc_hnl. Excludes 'hnl'/'hnlcosmic' -- those two are only ever populated by an
# MC-HNL sample itself (never mcbnb/dtbnb), and are passed separately via
# `hnl_categories=` for the HNL step overlay, so the stack's own dict has no reason to
# carry them.
background_categories_hnl = {k: v for k, v in signal_categories_hnl.items()
                              if k not in ('hnl', 'hnlcosmic')}

# Per-mass display scale for the HNL step overlay in plot_mc_hnl_data/plot_mc_hnl --
# how much to visually inflate a given mass point's histogram so it's visible next to
# the (much larger) MC background stack. Physically meaningless -- affects only
# `scale_hnl=`, not real event counts -- tuned by eye per mass point.
HNL_DISPLAY_SCALE = {
    140: 4000,
    165: 40,
    190: 10,
    215: 3,
    240: 2,
    260: 1,
}


def hnl_categories_for_mass(mass, simU, scale=None):
    """Build (scale, plotU, hnl_categories) for plot_mc_hnl_data/plot_mc_hnl's
    `scale_hnl=`/`hnl_categories=`, with the HNL legend entry relabeled to this mass's
    display-scaled |U|^2.

    `scale` defaults to HNL_DISPLAY_SCALE[mass] if not given explicitly.

    `hnl_categories` here is scoped to just the 'hnl' entry -- meant to be passed
    separately from `categories=background_categories_hnl`, since sharing one dict
    across both of plot_mc_hnl_data's internal plot_var calls means every category gets
    iterated (and potentially legended) by both calls.
    """
    from ...core.utils import sci_notation
    if scale is None:
        scale = HNL_DISPLAY_SCALE[mass]
    plotU = simU * np.sqrt(scale)
    hnllabel = (str(mass) + r' MeV HNL $\nu\pi^0$' + '\n'
                + r'|U$_{\mu 4}$|$^2$ = ' + str(sci_notation(plotU, 2, 2)))
    hnl_categories = {'hnl': {**signal_categories_hnl['hnl'], 'label': hnllabel}}
    return scale, plotU, hnl_categories


# ---------------------------------------------------------------------------
# PI0/HNL cut sequences (nu_pi0 topology -- distinct from nueCC's DEFAULT_CUTS,
# which uses nueCC-specific column names/thresholds not applicable here)
# ---------------------------------------------------------------------------

PI0_PRESEL_CUTS = [
    CutSpec("clear_cosmic", fn=lambda df: df.slc.is_clear_cosmic == 0,
            label="not clear cosmic"),
    CutSpec("nu_score", variable=("slc", "nu_score"), min=0.5,
            label="nu score > 0.5"),
    CutSpec("fiducial_volume",
            fn=lambda df: InFV(df.slc.vertex, det="SBND_nohighyz", inzback=0),
            label="fiducial volume (conditional xz/y box, y<100 for z>250)"),
]

PI0_CUTS_COMMON = PI0_PRESEL_CUTS + [
    CutSpec("flash_score", variable=("slc", "barycenterFM", "score"), min=0.02,
            label="flash match score > 0.02"),
    CutSpec("flash_time", variable=("slc", "barycenterFM", "flashTime_calib"),
            min=-250, max=2250, label="flash time in [-250, 2250] ns"),
    CutSpec("track_veto", fn=lambda df: df.slc.n_trks == 0,
            label="no reconstructed tracks"),
]

PI0_CUTS_1SHW = PI0_CUTS_COMMON + [
    CutSpec("n1shw", fn=lambda df: df.slc.n_shws == 1, label="exactly 1 shower"),
]
PI0_CUTS_2SHW = PI0_CUTS_COMMON + [
    CutSpec("n2shw", fn=lambda df: df.slc.n_shws == 2, label="exactly 2 showers"),
]

# Traditional angle cut, kept as a baseline to compare against a BDT (cut values from
# Lan's thesis).
PI0_CUTS_1SHW_ANGLE = PI0_CUTS_1SHW + [
    CutSpec("angle", variable=("primshw", "shw", "angle_z"), max=25, label="angle_z < 25 deg"),
]
PI0_CUTS_2SHW_ANGLE = PI0_CUTS_2SHW + [
    CutSpec("angle", variable=("primshw", "shw", "angle_z"), max=35, label="angle_z < 35 deg"),
]

# 'either_*' modes are the union (OR) of the two shower-multiplicity selections'
# tail cuts (the part beyond PI0_CUTS_COMMON) -- union_cut() folds that OR into a
# single CutSpec, so these are ordinary sequential (AND) CutSpec lists like every
# other entry in PI0_CUT_LISTS below, foldable into load-time cuts=.
PI0_CUTS_EITHER_SHW = PI0_CUTS_COMMON + [
    union_cut("either_shw", PI0_CUTS_1SHW[len(PI0_CUTS_COMMON):],
              PI0_CUTS_2SHW[len(PI0_CUTS_COMMON):],
              label="exactly 1 shower OR exactly 2 showers"),
]
PI0_CUTS_EITHER_ANGLE = PI0_CUTS_COMMON + [
    union_cut("either_angle", PI0_CUTS_1SHW_ANGLE[len(PI0_CUTS_COMMON):],
              PI0_CUTS_2SHW_ANGLE[len(PI0_CUTS_COMMON):],
              label="(1 shower, angle_z < 25 deg) OR (2 showers, angle_z < 35 deg)"),
]

PI0_CUT_LISTS = {
    'presel':       PI0_PRESEL_CUTS,
    '1shw':         PI0_CUTS_1SHW,
    '2shw':         PI0_CUTS_2SHW,
    '1shw_angle':   PI0_CUTS_1SHW_ANGLE,
    '2shw_angle':   PI0_CUTS_2SHW_ANGLE,
    'either_shw':   PI0_CUTS_EITHER_SHW,
    'either_angle': PI0_CUTS_EITHER_ANGLE,
}

def select_by_mode_pi0(df, mode):
    """Apply the named PI0/HNL selection to df. Single select() call for every mode
    (including 'either_shw'/'either_angle') -- foldable into load_mc/load_data/
    load_mchnl's own cuts= kwarg.
    """
    if mode not in PI0_CUT_LISTS:
        raise ValueError(f"mode must be one of {list(PI0_CUT_LISTS)}, got {mode!r}")
    return select(df, cuts=PI0_CUT_LISTS[mode])


# ---------------------------------------------------------------------------
# Truth categorisation
# ---------------------------------------------------------------------------

def define_signal_pi0(indf: pd.DataFrame, prefix=None):
    """Define signal/background categories for the generic pi0 analysis.

    Categorizes events into CCpi0 signal and various background categories
    based on truth information and fiducial volume, using the HNL/pi0 signal
    scheme (:data:`signal_dict_hnl`).

    Parameters
    ----------
    indf : pandas.DataFrame
        Input DataFrame with MultiIndex columns containing truth information.
    prefix : str or tuple, optional
        Column prefix to access truth information. If None, uses top-level columns.

    Returns
    -------
    pandas.DataFrame
        DataFrame with added 'signal' column indicating event category using
        ``signal_dict_hnl``.
    """
    from ...core.utils import ensure_lexsorted

    # Keep lexsorted axes for robust multi-index access without forcing a full copy.
    nudf = ensure_lexsorted(ensure_lexsorted(indf, 0), 1)

    if prefix is None:
        mcdf = nudf
    else:
        mcdf = nudf[prefix]

    whereFV = InFV(mcdf.position,det="SBND",inzback=0)
    whereAV = InAV(df=mcdf.position)
    whereCCpi0 = ((mcdf.iscc==1)  # require CC interaction
                & (abs(mcdf.pdg)==14)  # require neutrino to be a nue
                & (mcdf.npi0>0) # require at least one pi0 in the final state
                )

    if "signal" in nudf.columns:
        signal = nudf["signal"].to_numpy(copy=True)
    else:
        signal = np.full(len(nudf), -1, dtype=np.int16)

    # background
    signal[whereFV & (mcdf.iscc==0) & (mcdf.npi0 > 0)] = signal_dict_hnl["NCpi0"] # nc pi0 FV
    signal[whereFV & (mcdf.iscc==1) & (abs(mcdf.pdg)==14) & (mcdf.npi0 == 0)] = signal_dict_hnl["othernumuCC"] # numu cc other FV
    signal[whereFV & (mcdf.iscc==0) & (mcdf.npi0 == 0)] = signal_dict_hnl["otherNC"] # nc other FV
    signal[whereFV & (mcdf.iscc==1) & (abs(mcdf.pdg)==12)] = signal_dict_hnl["CCnue"] # nue cc FV
    signal[whereAV & (signal < 0)] = signal_dict_hnl["nonFV"] # nonFV
    signal[whereAV == False] = signal_dict_hnl["dirt"] # dirt
    signal[np.isnan(mcdf.E)] = signal_dict_hnl['cosmic']

    signal[whereFV & whereCCpi0] = signal_dict_hnl["CCpi0"]
    nudf["signal"] = signal
    if ((nudf.signal < 0) | (nudf.signal >= len(signal_dict_hnl))).any():
        print("Warning: unidentified signal/bacgkr channels present.")
    return nudf


def define_signal_hnl(indf):
    """Define signal for the HNL sample: everything (HNL and HNL cosmic) is signal."""
    signal_col = ('signal', '', '', '', '', '')
    # HNL cosmic (mask via slc.prtl.E == NaN) is deliberately labeled HNL too, not
    # signal_dict_hnl['hnlcosmic'] -- both are part of the signal region, so every row
    # gets the same value regardless of the cosmic mask (no need to branch on it).
    indf[signal_col] = signal_dict_hnl['hnl']

    return indf
