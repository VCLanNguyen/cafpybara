"""nueCC analysis configuration -- signal categories, cuts, and truth categorisation.

Shared/generic pieces (physical constants, generic_categories, pdg_categories,
mode_categories, category_dict_signal/control) live in
:mod:`cafpybara.core.physics` -- this file holds only what's genuinely
nueCC-specific.

**Customise the default cuts**::

    from cafpybara.analyses import nuecc
    from cafpybara.core.selection import modify_cut, select

    cuts = modify_cut(nuecc.DEFAULT_CUTS, "dedx", min=1.5, max=3.0)
    df_sel = select(df, cuts=cuts)

**Drop a cut**::

    cuts = drop_cuts(nuecc.DEFAULT_CUTS, "muon_rejection")
    cuts = drop_cuts(nuecc.DEFAULT_CUTS, "direction", "shower_length")

**Add a custom cut**::

    from cafpybara.core.classes import CutSpec
    cuts = nuecc.DEFAULT_CUTS + [CutSpec("my_cut", fn=lambda df: df.x > 10)]
"""

import numpy as np
import pandas as pd
from functools import partial
from makedf.util import InFV, InAV

from ...core.classes import CutSpec, VariableConfig
from ...core.selection import modify_cut, drop_cuts

__all__ = [
    'signal_categories', 'signal_categories_external', 'signal_dict',
    'cut_muon_rejection', 'InFiducial', 'InSpill', 'InScore',
    'DEFAULT_CUTS', 'SIDEBAND_CUTS',
    'define_signal',
    'electron_energy', 'electron_direction',
]


# ---------------------------------------------------------------------------
# Signal/background category definitions
# ---------------------------------------------------------------------------

# Signal == 0 is assumed to be the desired topology.
# Note: nonFV uses "C6" and dirt uses "C5" — intentionally non-sequential.
signal_categories = {
    "nueCC":       {"value": 0, "label": r"CC $\nu_e$",         "color": "C0"},
    "numuCCpi0":   {"value": 1, "label": r"CC $\nu_\mu\pi^0$",  "color": "C1"},
    "NCpi0":       {"value": 2, "label": r"NC $\nu$$\pi^0$",    "color": "C2"},
    "othernumuCC": {"value": 3, "label": r"other CC $\nu_\mu$", "color": "C3"},
    "othernueCC":  {"value": 4, "label": r"other CC $\nu_e$",   "color": "darkslateblue"},
    "otherNC":     {"value": 5, "label": r"other NC $\nu$",     "color": "C4"},
    "nonFV":       {"value": 6, "label": r"Non-FV $\nu$",       "color": "C6"},
    "dirt":        {"value": 7, "label": r"Dirt $\nu$",         "color": "C5"},
    "cosmic":      {"value": 8, "label": "cosmic",              "color": "darkgray"},
    "offbeam":     {"value": 9, "label": "offbeam",             "color": "lightgray"},
}
signal_dict = {k: v["value"] for k, v in signal_categories.items()}

# Simplified category scheme for external plots.  Each entry carries "values" (a list of
# signal_dict integers) rather than a single "value", so multiple internal categories are
# folded into one stack without modifying the signal column on the dataframe.
signal_categories_external = {
    "nueCC":        {"values": [0],    "label": r"CC $\nu_e$",         "color": "C0"},
    "numuCCpi0":    {"values": [1],    "label": r"CC $\nu_\mu\pi^0$",  "color": "C1"},
    "NCpi0":        {"values": [2],    "label": r"NC $\nu\pi^0$",      "color": "C2"},
    "other_nu":     {"values": [3,4,5],"label": r"other $\nu$",        "color": "C3"},
    "nonFV_dirt":   {"values": [6,7],  "label": r"non-FV $\nu$",       "color": "C5"},
    "cosmic_bkg":   {"values": [8,9],  "label": "cosmic",              "color": "darkgray"},
}


# ---------------------------------------------------------------------------
# Cut helper functions
# ---------------------------------------------------------------------------

# "SBND_nohighyz" (not the original nueana's "SBND_nu26") -- "SBND_nu26" was
# never a valid `det` value in cafpyana's makedf.util.InFV (checked full git
# history, zero hits), so nueCC's DEFAULT_CUTS chain never actually worked
# against this cafpyana repo. Fixed 2026-07-14 per user's physics judgment.
FV_DET    = "SBND_nohighyz"
FV_INZBACK = 0


def InFiducial(position):
    """Fiducial volume cut applied uniformly across selection and signal definition."""
    return InFV(position, det=FV_DET, inzback=FV_INZBACK)


def cut_muon_rejection(df, max_track_length=200):
    return np.isnan(df.primtrk.trk.len) | (df.primtrk.trk.len < max_track_length)


def InSpill(df, spill_start=0.335, spill_end=0.335 + 1.6):
    return (
        (df.slc.barycenterFM.flashTime > spill_start)
        & (df.slc.barycenterFM.flashTime < spill_end)
    )


def InScore(df, score_cut=0.02):
    return df.slc.barycenterFM.score > score_cut


# ---------------------------------------------------------------------------
# Default cut sequence
# ---------------------------------------------------------------------------

DEFAULT_CUTS = [
    CutSpec("flash_pe",        variable=("slc", "barycenterFM", "flashPEs"),  min=2e3,              label="flash PE > 2000"),
    CutSpec("nu_score",        variable=("slc", "nu_score"),                  min=0.5,              label="nu score > 0.5"),
    CutSpec("clear_cosmic",    fn=lambda df: df.slc.is_clear_cosmic == 0,                           label="not clear cosmic"),
    CutSpec("flash_time",      variable=("slc", "barycenterFM", "flashTime"), min=0.335, max=1.935, label="flash time [0.335, 1.935] µs"),
    CutSpec("flash_score",     variable=("slc", "barycenterFM", "score"),     min=0.02,             label="flash score > 0.02"),
    CutSpec("fiducial_volume", fn=lambda df: InFiducial(df.slc.vertex),                             label="fiducial volume"),
    CutSpec("contained",       fn=lambda df: df.slc.contained.margin_5.tot==True,                   label="contained (5cm margin)"),
    CutSpec("nohighyz",        fn=lambda df: df.slc.pfp_notinhigh==True,                            label="highyz activity veto"),
    CutSpec("shower_energy",   variable=("primshw", "shw", "reco_energy"),    min=0.5,              label="shower energy > 0.5 GeV"),
    CutSpec("muon_rejection",  fn=cut_muon_rejection,                                               label="track length < 200 cm"),
    CutSpec("conversion_gap",  variable=("primshw", "shw", "conversion_gap"), min=0.001, max=2,     label="conversion gap [0.001, 2] cm"),
    CutSpec("dedx",            variable=("primshw", "shw", "bestplane_dEdx"), min=1.25,  max=2.5,   label="dE/dx [1.25, 2.5] MeV/cm"),
    CutSpec("opening_angle",   variable=("primshw", "shw", "open_angle"),     min=0.03,  max=0.15,  label="opening angle [0.03, 0.15] rad"),
    CutSpec("shower_length",   variable=("primshw", "shw", "len"),            min=10,    max=200,   label="shower length [10, 200] cm"),
]

# Sideband: built from DEFAULT_CUTS by overriding the cuts that differ.
SIDEBAND_CUTS = DEFAULT_CUTS.copy()
SIDEBAND_CUTS = drop_cuts(SIDEBAND_CUTS, "muon_rejection")
SIDEBAND_CUTS = drop_cuts(SIDEBAND_CUTS, "shower_length")
SIDEBAND_CUTS = modify_cut(SIDEBAND_CUTS, "conversion_gap", min=2,   max=np.inf, label="conversion gap > 2 cm")
SIDEBAND_CUTS = modify_cut(SIDEBAND_CUTS, "dedx",           min=3,   max=6,      label="dE/dx [3, 6] MeV/cm")
SIDEBAND_CUTS = modify_cut(SIDEBAND_CUTS, "opening_angle",  min=0,   max=1.0,    label="opening angle [0, 1.0] rad")


# ---------------------------------------------------------------------------
# Truth categorisation
# ---------------------------------------------------------------------------

def define_signal(indf: pd.DataFrame, prefix=None):
    """Define signal/background categories for neutrino interactions.

    Categorizes events into signal (CC nue) and background categories
    based on truth information and fiducial volume.

    Parameters
    ----------
    indf : pandas.DataFrame
        Input DataFrame with MultiIndex columns containing truth information.
    prefix : str or tuple, optional
        Column prefix to access truth information. If None, uses top-level columns.

    Returns
    -------
    pandas.DataFrame
        DataFrame with added ``signal`` column (values from ``signal_dict``).
    """
    from ...core.utils import ensure_lexsorted
    nudf = ensure_lexsorted(ensure_lexsorted(indf, 0), 1)

    mcdf = nudf[prefix] if prefix is not None else nudf

    whereFV = InFiducial(mcdf.position)
    whereAV = InAV(df=mcdf.position)
    whereCCnue = (
        (mcdf.iscc == 1)
        & (abs(mcdf.pdg) == 12)
        & (abs(mcdf.e.pdg) == 11)
        & (mcdf.e.genE > 0.5)
    )

    if "signal" in nudf.columns:
        signal = nudf["signal"].to_numpy(copy=True)
    else:
        signal = np.full(len(nudf), -1, dtype=np.int16)

    signal[whereFV & (mcdf.iscc == 1) & (abs(mcdf.pdg) == 14) & (mcdf.npi0 > 0)]   = signal_dict["numuCCpi0"]
    signal[whereFV & (mcdf.iscc == 0) & (mcdf.npi0 > 0)]                           = signal_dict["NCpi0"]
    signal[whereFV & (mcdf.iscc == 1) & (abs(mcdf.pdg) == 12)]                     = signal_dict["othernueCC"]
    signal[whereFV & (mcdf.iscc == 1) & (abs(mcdf.pdg) == 14) & (mcdf.npi0 == 0)]  = signal_dict["othernumuCC"]
    signal[whereFV & (mcdf.iscc == 0) & (mcdf.npi0 == 0)]                          = signal_dict["otherNC"]
    signal[whereAV & (signal < 0)]                                                 = signal_dict["nonFV"]
    signal[whereAV == False]                                                       = signal_dict["dirt"]
    signal[np.isnan(mcdf.E)]                                                       = signal_dict['cosmic']
    signal[whereFV & whereCCnue]                                                   = signal_dict["nueCC"]

    nudf["signal"] = signal
    if ((nudf.signal < 0) | (nudf.signal >= len(signal_dict))).any():
        print("Warning: unidentified signal/background channels present.")
    return nudf


# ---------------------------------------------------------------------------
# Analysis variables
# ---------------------------------------------------------------------------

def electron_energy() -> VariableConfig:
    """VariableConfig for primary electron energy (GeV)."""
    return VariableConfig(
        var_save_name="energy",
        var_plot_name="$E_{e-}$",
        var_unit="GeV",
        bins=np.array([0.5, 0.7, 0.95, 1.25, 1.7, 2.5]),
        bin_labels=np.array([0.5, 0.7, 0.95, 1.25, 1.7, 5]),
        var_evt_reco_col=('primshw', 'shw', 'reco_energy'),
        var_evt_truth_col=('slc', 'truth', 'e', 'genE'),
        var_nu_col=('e', 'genE'),
    )


def electron_direction() -> VariableConfig:
    """VariableConfig for primary electron direction (cos theta)."""
    return VariableConfig(
        var_save_name="direction",
        var_plot_name="$\\cos\\theta_{e-}$",
        var_unit="",
        bins=np.array([0.5, 0.6, 0.75, 0.85, 0.925, 1.0]),
        bin_labels=np.array([-1.0, 0.6, 0.75, 0.85, 0.925, 1.0]),
        var_evt_reco_col=('primshw', 'shw', 'dir', 'z'),
        var_evt_truth_col=('slc', 'truth', 'e', 'dir', 'z'),
        var_nu_col=('e', 'dir', 'z'),
    )
