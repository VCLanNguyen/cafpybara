"""HNL/pi0-specific paths.

HNL/pi0-topology detvar store (produced via hnl_mcnu_detvar.py +
process_detvars.py --village hnlpi0 -s preprocess), built from the
concatenated detvar_cv_0/detvar_0p94xly_0/detvar_1p19xly_0 samples. Since
HNL/pi0 has no fixed DEFAULT_CUTS-style cut sequence (cuts are built per-mode
via PI0_CUT_LISTS), only the preprocess-only store is meaningful; apply the
real HNL/pi0 cuts at analysis time via
get_total_cov(..., cuts=<hnlpi0_cuts>, detvar_files=HNL_DETVAR_DICT_FILES).

No in-time-cosmic file exists for this topology yet -- requesting 'cosmic'
in uncertainty_keys will raise (see funcs.get_total_cov).
"""

HNL_DETVAR_DIR = "/exp/sbnd/data/users/lnguyen/cafpyana_pi0/dataframes/July2026/detvar"
HNL_DETVAR_DICT_FILES = [HNL_DETVAR_DIR + "/detvars.h5",]
