#!/usr/bin/env python
"""Build detector variation HDF5 stores with preprocessing and optional selection.

Loads all ``detvar_<name>_<idx>.df`` files in the input directory.  Files
whose base name is ``cv`` are treated as CV samples; all others are DV
samples.  Files sharing the same base name are grouped into a list (multisim
pairs when two universes exist).  The CV mapping is derived automatically:
every DV maps to the CV key specified by ``--cv-key`` (default: the first CV
found in the directory).

Recombination detector variations are built from the reference CV and added
to the DV set automatically.

Unlike the original nueCC-only version, this script has no default topology
-- pass ``--village nuecc`` or ``--village hnlpi0`` to select which
analysis's ``slc_key``/preprocessing/selection presets to use. A future
topology's own village just needs `select`/`select_sideband`/`preprocess_mc`
(or equivalents) importable the same way.

Selection types
---------------
preprocess  Preprocessing only (no cut-based selection); output: detvars.h5
signal      Full signal selection via select(); output: detvars_signal.h5
sideband    Sideband selection via select_sideband(); output: detvars_sideband.h5
preselect   Signal selection stopped at shower_energy stage; output: detvars_preselect.h5
all         All four of the above.

Note: 'signal'/'sideband'/'preselect' presets are only meaningful for
villages that define select_sideband and a single obviously-correct default
cut list (today: nuecc). hnlpi0 has multiple valid cut-list modes with no
single default -- use '-s preprocess' only for hnlpi0, and apply the real
cut sequence later via get_total_cov(..., cuts=<hnl_cuts>).

Examples
--------
    # nueCC: signal + sideband stores (default selections)
    python process_detvars.py --village nuecc -i /path/to/dfs/ -o /path/to/output/

    # HNL/pi0: preprocess-only store
    python process_detvars.py --village hnlpi0 -i /path/to/dfs/ -o /path/to/output/ -s preprocess
"""
from __future__ import annotations

import argparse
import importlib
import os
import re
import sys

from cafpybara.core import detvar as core_detvar
from cafpybara.core.selection import select as core_select

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OUTPUT_FILE = {
    "preprocess": "detvars.h5",
    "signal":     "detvars_signal.h5",
    "sideband":   "detvars_sideband.h5",
    "preselect":  "detvars_preselect.h5",
}

_ALL_SELECTIONS = ["preprocess", "signal", "sideband", "preselect"]

_DETVAR_RE = re.compile(r'^detvar_(.+)_(\d+)\.df$')

_UNSET = object()

_SLC_KEY = {
    "nuecc":  "nuecc",
    "hnlpi0": "rec",
}


def _load_village(name):
    return importlib.import_module(f"cafpybara.analyses.{name}")


def _default_preprocess_fn(village_name, village):
    if village_name == "nuecc":
        return village.preprocess.preprocess_mc
    if village_name == "hnlpi0":
        return village.preprocess.preprocess_mcbnb
    raise ValueError(f"No default preprocess_fn known for village '{village_name}'")


def _selection_fn_map(village_name, village):
    """Map selection-type name -> (cuts, stage). 'preprocess' is always (None, None).

    Resolves nueCC's DEFAULT_CUTS/SIDEBAND_CUTS explicitly here, rather than
    going through village.select's own cuts=None defaulting -- so the exact
    resolved cut-name list used to build each store is known at this call
    site, which is what gets stamped into the store as cuts_signature below
    (lets get_detvar_systs later detect store/cuts drift, e.g. a cut's
    definition changing after the store was built).
    """
    out = {"preprocess": (None, None)}
    if village_name == "nuecc":
        out["signal"]    = (village.DEFAULT_CUTS, None)
        out["sideband"]  = (village.SIDEBAND_CUTS, None)
        out["preselect"] = (village.DEFAULT_CUTS, "shower_energy")
    return out


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _parse_detvar_files(input_dir: str) -> tuple[dict, dict]:
    """Scan input_dir and split detvar_<name>_<idx>.df files into CV and DV groups.

    Each DV file is stored as its own entry keyed by ``<name>_<idx>`` so the
    index can be used to look up the matching CV.  Files whose base name is
    ``cv`` are treated as CV samples.

    Returns
    -------
    cv_files : dict[str, str]
        {cv_key: filepath}  e.g. {'cv_0': '/path/detvar_cv_0.df'}
    dv_files : dict[str, tuple[str, int]]
        {dv_key: (filepath, idx)}  e.g. {'wiremodxw_1': ('/path/...', 1)}
    """
    cv_files: dict[str, str]          = {}
    dv_files: dict[str, tuple]        = {}

    for fname in sorted(os.listdir(input_dir)):
        m = _DETVAR_RE.match(fname)
        if not m:
            continue
        base, idx = m.group(1), int(m.group(2))
        fpath = os.path.join(input_dir, fname)
        if base == "cv":
            cv_files[f"cv_{idx}"] = fpath
        else:
            dv_files[f"{base}_{idx}"] = (fpath, idx)

    return cv_files, dv_files


# ---------------------------------------------------------------------------
# Dict builders
# ---------------------------------------------------------------------------

def build_dicts(input_dir: str, village, village_name: str, cv_key: str | None = None,
                 slc_key: str | None = None, preprocess_fn=_UNSET):
    """Load all CV and DV files; attach recombination detvars.

    Parameters
    ----------
    input_dir : str
        Directory containing detvar_<name>_<idx>.df files.
    village : module
        The imported `cafpybara.analyses.<name>` village module.
    village_name : str
        Name of the village (e.g. 'nuecc', 'hnlpi0') -- used to resolve the
        default slc_key/preprocess_fn if not given explicitly.
    cv_key : str, optional
        Key of the CV used as the reference for DV matching and recombination
        variations.  Defaults to the lexicographically first CV key found.
    slc_key : str, optional
        Table key for the slice-level analysis DataFrame within each raw
        ``.df`` file. Defaults to ``_SLC_KEY[village_name]``.
    preprocess_fn : callable or None, optional
        Called as ``preprocess_fn(slc_df)`` on each CV/DV's slice-level table
        before it's stored. Defaults to the village's own base MC
        preprocessing function. Pass an explicit callable to override, or
        ``None`` to force-skip preprocessing.

    Returns
    -------
    cv_dict, dv_dict, cv_map
    """
    cv_files, dv_files = _parse_detvar_files(input_dir)

    if not cv_files:
        sys.exit("ERROR: no CV files found (expected detvar_cv_<idx>.df)")
    if not dv_files:
        print("WARNING: no DV files found.")

    available_cv_keys = sorted(cv_files.keys())
    if cv_key is None:
        cv_key = available_cv_keys[0]
    elif cv_key not in cv_files:
        sys.exit(
            f"ERROR: CV key '{cv_key}' not found. "
            f"Available: {available_cv_keys}"
        )

    if slc_key is None:
        slc_key = _SLC_KEY[village_name]
    if preprocess_fn is _UNSET:
        preprocess_fn = _default_preprocess_fn(village_name, village)

    def _load_preprocessed(path):
        dvf = core_detvar.prepare_detvar_df(path, slc_key=slc_key)
        if preprocess_fn is not None:
            dvf = dvf._replace(slc_df=preprocess_fn(dvf.slc_df))
        return dvf

    cv_dict: dict = {}
    for key, path in sorted(cv_files.items()):
        print(f"Loading CV '{key}': {path}")
        cv_dict[key] = _load_preprocessed(path)

    dv_dict: dict = {}
    cv_map:  dict = {}
    for key, (path, idx) in sorted(dv_files.items()):
        mapped_cv = f"cv_{idx}"
        if mapped_cv not in cv_dict:
            sys.exit(
                f"ERROR: DV '{key}' expects CV '{mapped_cv}' but it was not found. "
                f"Available CVs: {sorted(cv_dict.keys())}"
            )
        print(f"  Loading DV '{key}' → CV '{mapped_cv}'")
        dv_dict[key] = _load_preprocessed(path)
        cv_map[key]  = mapped_cv

    ref_cv = cv_dict[cv_key]
    print(f"\nBuilding recombination detvars from '{cv_key}'...")
    recomb_dfs = core_detvar.make_recomb_detvars(ref_cv.slc_df)
    recomb = {
        name: [ref_cv._replace(slc_df=df) for df in dfs]
        for name, dfs in recomb_dfs.items()
    }
    dv_dict.update(recomb)
    cv_map.update({name: cv_key for name in recomb})
    print(f"  Recomb variations: {list(recomb.keys())}")

    return cv_dict, dv_dict, cv_map


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--village",
        required=True,
        choices=sorted(_SLC_KEY),
        help="Which cafpybara.analyses village to build the store for.",
    )
    parser.add_argument(
        "-i", "--input-dir",
        required=True,
        dest="input_dir",
        help="Directory containing detvar_<name>_<idx>.df files.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        required=True,
        dest="output_dir",
        help="Directory to write output .h5 stores.",
    )
    parser.add_argument(
        "--selections", "-s",
        nargs="+",
        choices=_ALL_SELECTIONS + ["all"],
        default=["signal", "sideband"],
        metavar="SELECTION",
        help=(
            "Which stores to write. Choices: "
            + ", ".join(_ALL_SELECTIONS)
            + ", all (shorthand for all four). Default: signal sideband "
            "(only valid for villages with select_sideband, e.g. nuecc)."
        ),
    )
    parser.add_argument(
        "--cv-key",
        default=None,
        help=(
            "CV key to use as the reference for DV matching and recombination "
            "variations (e.g. 'cv_0'). Defaults to the first CV key found."
        ),
    )
    parser.add_argument(
        "--slc-key",
        dest="slc_key",
        default=None,
        help=(
            "Table key for the slice-level analysis DataFrame within each raw "
            "detvar_*.df file. Defaults to the village's own convention "
            "('nuecc' for --village nuecc, 'rec' for --village hnlpi0)."
        ),
    )
    parser.add_argument(
        "--groups", "-g",
        nargs="+",
        default=None,
        metavar="GROUP",
        help=(
            "Subset of DV group names to (re)compute. When omitted, all groups are "
            "built. When specified, only the listed groups are written; if the output "
            "file already exists the other groups are left untouched (append mode). "
            "Example: -g recomb_lo recomb_hi wiremodxw_0"
        ),
    )
    args = parser.parse_args()

    selections = _ALL_SELECTIONS if "all" in args.selections else args.selections

    village = _load_village(args.village)
    selection_fn_map = _selection_fn_map(args.village, village)
    unsupported = set(selections) - set(selection_fn_map)
    if unsupported:
        sys.exit(
            f"ERROR: village '{args.village}' does not support selection type(s) "
            f"{sorted(unsupported)} -- only {sorted(selection_fn_map)} available. "
            "See module docstring."
        )

    os.makedirs(args.output_dir, exist_ok=True)

    cv_dict, dv_dict, cv_map = build_dicts(
        args.input_dir, village, args.village, cv_key=args.cv_key, slc_key=args.slc_key,
    )
    print(f"\nCV keys : {list(cv_dict.keys())}")
    print(f"DV keys : {list(dv_dict.keys())}")
    print(f"CV map  : {cv_map}")

    write_mode = 'w'
    if args.groups is not None:
        expanded: set[str] = set()
        for name in args.groups:
            if name in cv_dict:
                matched = {g for g, ck in cv_map.items() if ck == name}
                print(f"  '{name}' → {sorted(matched)}")
                expanded |= matched
            else:
                expanded.add(name)
        unknown = expanded - set(dv_dict)
        if unknown:
            print(f"\nWARNING: requested groups not found: {sorted(unknown)}")
        keep = expanded & set(dv_dict)
        dv_dict = {k: v for k, v in dv_dict.items() if k in keep}
        cv_map  = {k: v for k, v in cv_map.items()  if k in keep}
        needed_cvs = set(cv_map.values())
        cv_dict = {k: v for k, v in cv_dict.items() if k in needed_cvs}
        write_mode = 'a'
        print(f"\nFiltered to groups : {sorted(dv_dict.keys())}")
        print(f"Write mode         : append (patch existing store)")

    for sel_name in selections:
        out_path = os.path.join(args.output_dir, _OUTPUT_FILE[sel_name])
        print(f"\n[{sel_name}] → {out_path}")
        cuts, stage = selection_fn_map[sel_name]
        if cuts is None:
            core_detvar.write_detvar_store(out_path, cv_dict, dv_dict, cv_map, mode=write_mode)
        else:
            cv_sel = core_detvar.apply_selection(cv_dict, core_select, cuts=cuts, stage=stage)
            dv_sel = core_detvar.apply_selection(dv_dict, core_select, cuts=cuts, stage=stage)
            cuts_signature = [c.name for c in cuts]
            core_detvar.write_detvar_store(out_path, cv_sel, dv_sel, cv_map, mode=write_mode,
                                            cuts_signature=cuts_signature, stage=stage)

    print("\nDone.")


if __name__ == "__main__":
    main()
