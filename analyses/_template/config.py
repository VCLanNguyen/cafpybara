"""TEMPLATE -- your analysis's own file paths.

Every value below is a deliberately-broken placeholder (an obviously-fake
path, not `None` and not a real HNL/nueCC path), so unfilled use fails
loud (`FileNotFoundError` or similar) instead of silently reading someone
else's data.
"""

# TODO: set your detvar store directory (see hnlpi0/nuecc config.py).
DETVAR_DIR = "TODO_SET_ME/replace_with_your_real_detvar_directory"
DETVAR_DICT_FILES = [DETVAR_DIR + "/detvars.h5"]

# TODO: set if you have a real in-time-cosmic sample, else leave None.
INTIME_FILE = None
