"""Detector/beam physical constants and topology-independent category schemes.

Everything here describes the SBND detector or the BNB beam, or is a broad
classification scheme not tied to a specific analysis's signal definition --
none of it is specific to nueCC, HNL/pi0, or any future topology.
"""

import uproot
import seaborn as sns
import numpy as np
import pandas as pd
from makedf.util import InFV, InAV

from . import config
from .utils import ensure_lexsorted

__all__ = [
    'RHO', 'N_A', 'M_AR', 'V_SBND', 'NTARGETS',
    'nue_flux', 'flux_vals', 'integrated_flux',
    'POT_NORM_UNC', 'NTARGETS_UNC',
    'generic_categories', 'generic_dict', 'define_generic',
    'pdg_categories', 'pdg_dict',
    'mode_categories', 'mode_dict',
    'category_dict_signal', 'category_dict_control',
]

# ---------------------------------------------------------------------------
# Physical and detector constants
# ---------------------------------------------------------------------------

RHO = 1.3836        # g/cm3, liquid Ar density
N_A = 6.02214076e23 # Avogadro's number
M_AR = 40           # g, molar mass of argon
# x cm (drift) * z cm (width) * y cm (height), excluding 90 cm of y-dimension at high z
V_SBND = (190)*2 * ((250 - 10)*(190*2) + (450-250)*(100 + 190))
NTARGETS = RHO * V_SBND * N_A / M_AR

# flux file, units: /m^2/10^6 POT, 50 MeV bins
with uproot.open(config.FLUX_FILE) as f:
    nue_flux = f["flux_sbnd_nue"].to_numpy()
    flux_vals = nue_flux[0]
integrated_flux = flux_vals.sum() / 1e4               # convert to cm^-2
integrated_flux *= (180*180) / (200*200)               # rescale front face to AV front face

POT_NORM_UNC  = 0.02  # fractional uncertainty on beam exposure (POT counting)
NTARGETS_UNC  = 0.01  # fractional uncertainty on number of Ar targets

# ---------------------------------------------------------------------------
# Broad (topology-independent) category schemes
# ---------------------------------------------------------------------------

generic_categories = {
    "CCnu":   {"value": 0, "label": r"CC $\nu$",     "color": "C3"},
    "NCnu":   {"value": 1, "label": r"NC $\nu$",     "color": "darkslateblue"},
    "nonFV":  {"value": 2, "label": r"Non-FV $\nu$", "color": "C5"},
    "dirt":   {"value": 3, "label": r"Dirt $\nu$",   "color": "C6"},
    "cosmic": {"value": 4, "label": "cosmic",        "color": "C7"},
}
generic_dict = {k: v["value"] for k, v in generic_categories.items()}


def define_generic(indf: pd.DataFrame, prefix=None):
    """Define broad signal/background categories (CC nu, NC nu, non-FV, dirt, cosmic).

    Parameters
    ----------
    indf : pandas.DataFrame
        Input DataFrame with MultiIndex columns containing truth information.
    prefix : str or tuple, optional
        Column prefix to access truth information. If None, uses top-level columns.

    Returns
    -------
    pandas.DataFrame
        DataFrame with added ``signal`` column (values from ``generic_dict``).
    """
    indf = ensure_lexsorted(indf, 0)
    nudf = ensure_lexsorted(indf.copy(), 1)

    mcdf = nudf[prefix] if prefix is not None else nudf

    whereFV = InFV(df=mcdf.position, inzback=0, det="SBND")
    whereAV = InAV(df=mcdf.position)

    if "signal" not in nudf.columns:
        nudf["signal"] = -1

    nudf["signal"] = np.where(whereAV == False,           generic_dict["dirt"],   nudf["signal"])
    nudf["signal"] = np.where(whereAV,                    generic_dict["nonFV"],  nudf["signal"])
    nudf["signal"] = np.where(whereFV & (mcdf.iscc == 0), generic_dict["NCnu"],   nudf["signal"])
    nudf["signal"] = np.where(whereFV & (mcdf.iscc == 1), generic_dict["CCnu"],   nudf["signal"])
    nudf["signal"] = np.where(np.isnan(mcdf.E),           generic_dict["cosmic"], nudf["signal"])

    if ((nudf.signal < 0) | (nudf.signal >= len(generic_dict))).any():
        print("Warning: unidentified signal/background channels present.")
    indf["signal"] = nudf["signal"]
    return indf


# PDG categories for plotting. The 5 named entries use pdg-code filtering; the 4
# extras (pdg=None) use filter-based population selection. Insertion order matters:
# named entries must precede extras so that "other_nu" is built from the remainder.
pdg_categories = {
    r"$e$":            {"pdg": 11,   "color": "C0"},
    r"$\mu$":          {"pdg": 13,   "color": "C1"},
    r"$\gamma$":       {"pdg": 22,   "color": "C2"},
    r"$p$":            {"pdg": 2212, "color": "C3"},
    r"$\pi^{+/-}$":    {"pdg": 211,  "color": "darkslateblue"},
    r"non-$\nu$ $e$":  {"pdg": None, "color": "C4",       "filter": "notprim"},
    "cosmic":          {"pdg": None, "color": "darkgray",  "filter": "cosmic"},
    "offbeam":         {"pdg": None, "color": "lightgray", "filter": "offbeam"},
    "other":           {"pdg": None, "color": "sienna",    "filter": "other_nu"},
}
pdg_dict = pdg_categories

_mode_palette = sns.color_palette("Dark2", n_colors=7)
mode_categories = {
    "QE":            {"value": 0,    "color": _mode_palette[0]},
    "RES":           {"value": 1,    "color": _mode_palette[1]},
    "DIS":           {"value": 2,    "color": _mode_palette[2]},
    "COH":           {"value": 3,    "color": _mode_palette[3]},
    "MEC":           {"value": 10,   "color": _mode_palette[4]},
    r"other $\nu$":  {"value": None, "color": _mode_palette[5], "filter": "other_nu"},
    r"non $\nu$":    {"value": None, "color": "darkgray",       "filter": "non_nu"},
}
mode_dict = {k: v["value"] for k, v in mode_categories.items() if v["value"] is not None}

category_dict_signal = {
    'GENIE':        {'color': 'C0',        'label': 'GENIE', 'line': '-'},
    'Flux':         {'color': 'seagreen',  'label': 'Flux', 'line': '-'},
    'DetVar':       {'color': 'orange',    'label': 'Detector Variations', 'line': '-'},
    'Geant4':       {'color': 'red',       'label': 'G4', 'line': '-'},
    'BeamExposure': {'color': 'deeppink',  'label': 'Beam Exposure', 'line': '-'},
    'NTargets':     {'color': 'purple',    'label': 'NTargets', 'line': '-'},
    'Cosmic':       {'color': 'sienna',    'label': 'Cosmic', 'line': '-'},
    'MCstat':       {'color': 'slategray', 'label': 'MC statistics', 'line': '-'},
    'Datastat':     {'color': 'gray',      'label': 'Data statistics\n[proj. 1e20 POT]', 'line': '--'},
}

category_dict_control = {
    'GENIE':        {'color': 'navy',            'label': 'GENIE', 'line': '-'},
    'Flux':         {'color': 'darkgreen',       'label': 'Flux', 'line': '-'},
    'DetVar':       {'color': 'darkorange',      'label': 'Detector Variations', 'line': '-'},
    'Geant4':       {'color': 'firebrick',       'label': 'G4', 'line': '-'},
    'BeamExposure': {'color': 'mediumvioletred', 'label': 'Beam Exposure', 'line': '-'},
    'NTargets':     {'color': 'rebeccapurple',   'label': 'NTargets', 'line': '-'},
    'Cosmic':       {'color': 'saddlebrown',     'label': 'Cosmic', 'line': '-'},
    'MCstat':       {'color': 'slategray',       'label': 'MC statistics', 'line': '-'},
    'Datastat':     {'color': 'gray',            'label': 'Data statistics\n[proj. 1e20 POT]', 'line': '--'},
}
