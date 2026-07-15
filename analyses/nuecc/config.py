"""nueCC-specific paths (detvar/in-time-cosmic stores built with this village's own cuts)."""

# In-time cosmic sample file path
INTIME_FILE = "/exp/sbnd/data/users/lynnt/xsection/samples/MCP2025B_v10_06_00_09/dfs_nu26/mc_intime.df"

# Detector variation (detvar) dictionaries path.
# Built with nueCC's own DEFAULT_CUTS/SIDEBAND_CUTS -- not usable as-is for
# any other topology (see cafpybara.analyses.hnlpi0.config.HNL_DETVAR_DICT_FILES).
DETVAR_DICT_DIR = "/exp/sbnd/data/users/lynnt/xsection/samples/MCP2025B_v10_06_00_09/dfs_nu26/detvars"
DETVAR_DICT_FILES = [DETVAR_DICT_DIR + "/detvars.h5",]
DETVAR_DICT_SIGNAL = DETVAR_DICT_DIR + "/detvars_signal.h5"
DETVAR_DICT_CONTROL = DETVAR_DICT_DIR + "/detvars_sideband.h5"
