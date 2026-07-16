"""TEMPLATE -- your analysis's own file paths.

Every value below is a deliberately-broken placeholder (an obviously-fake
path, not `None` and not a real HNL/nueCC path) -- if you copy this
directory without editing these, code that actually tries to use them will
fail loudly (FileNotFoundError or similar) instead of silently reading
someone else's data. That's intentional: a silently-wrong default is
exactly the bug class this whole template exists to prevent -- see
`examples/build_a_new_analysis.ipynb`.
"""

# TODO: your own detector-variation store directory (built via
# core/detvar/process_detvars.py --analysis <you> -s preprocess). See
# hnlpi0/config.py or nuecc/config.py for real, working examples.
DETVAR_DIR = "TODO_SET_ME/replace_with_your_real_detvar_directory"
DETVAR_DICT_FILES = [DETVAR_DIR + "/detvars.h5"]

# TODO: if your topology has an in-time-cosmic sample, point at it here and
# thread it through your systs_input() factory (see funcs.py). If it
# doesn't exist yet, leave this as None -- your systs_input() should raise
# a clear error if 'cosmic' is requested, the same way hnlpi0's does.
INTIME_FILE = None
