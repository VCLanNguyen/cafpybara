"""Shared, topology-independent paths.

Analysis-specific paths (detvar dictionaries, in-time cosmic files, etc.) live
in each analysis's own `cafpybara/analyses/<topology>/config.py`, not here.
"""

# Flux file path -- same BNB flux regardless of analysis topology.
# units: /m^2/10^6 POT, 50 MeV bins
FLUX_FILE = "/exp/sbnd/data/users/lynnt/xsection/flux/sbnd_original_flux.root"
