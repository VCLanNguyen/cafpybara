from datetime import datetime
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Generic timing-calibration engines
# ---------------------------------------------------------------------------

def timing_correction(indf, period=18.936, t0_offset=0, prefix='', ifData=False):

    var_name = 'flashTime_'+prefix
    var_col = ('slc', 'barycenterFM', var_name, '', '', '')
    mod_col = ('slc', 'barycenterFM', var_name+'_mod', '', '', '')

    if ifData:
        base = indf.slc.barycenterFM.flashTime + indf.frameApplyAtCaf/1e3
    else:
        base = indf.slc.barycenterFM.flashTime

    corrected = base*1000 - indf.slc.vertex.z/29.97 + t0_offset + period/2
    indf[var_col] = corrected

    indf[mod_col] = corrected % period
    return indf

def data_filter_bad(indf, bad_dict):

    nfilter = 0

    for k,v in bad_dict.items():
        tmin = v[0]
        tmax = v[1]

        tdc = indf['tdcRwm'].astype(np.int64)
        mask = (tdc >= tmin) & (tdc <= tmax)
        nfilter += (len(indf[mask]))
        indf = indf[~mask]

    print(' Remove {:.0f} slices'.format(nfilter))

    return indf

def data_correct_good(indf, good_dict, odict, pdict):

    ncorrect = 0
    df_list = []

    tdc = indf['tdcRwm'].astype(np.int64)

    for k,v in good_dict.items():
        tmin = v[0]
        tmax = v[1]

        mask = (tdc >= tmin) & (tdc <= tmax)

        df_chunk = indf[mask]
        ncorrect += (len(df_chunk))

        data_first_peak = odict[k]
        data_period = pdict[k]

        df_chunk = timing_correction(df_chunk, period=data_period, t0_offset=data_first_peak, prefix='calib', ifData=True)

        df_list.append(df_chunk)

    print(' Correct {:.0f} slices'.format(ncorrect))

    return pd.concat(df_list)


# ---------------------------------------------------------------------------
# Run/period boundaries
# ---------------------------------------------------------------------------

tmin_run1 = datetime(2025, 2, 10, 0, 0, 0)
tmax_run1 = datetime(2025, 7, 8, 23, 59, 59)

tmin_period1a = tmin_run1.timestamp() * 1e9
tmax_period1a = datetime(2025,2,16, 9,43,00).timestamp()*1e9

tmin_period1b = tmax_period1a
tmax_period1b = datetime(2025,2,16, 19,00,00).timestamp()*1e9

tmin_period1c = tmax_period1b
tmax_period1c = datetime(2025,2,20, 2,47,00).timestamp()*1e9

tmin_period1d = tmax_period1c 
tmax_period1d = datetime(2025, 4, 2, 16, 57, 0).timestamp() * 1e9
tmin_rotation = tmax_period1d
tmax_rotation = datetime(2025, 4, 7, 16, 1, 00).timestamp() * 1e9

tmin_period3a = tmax_rotation
tmax_period3a = datetime(2025, 4,23, 17,50,0).timestamp() *1e9

tmin_period3b = tmax_period3a
tmax_period3b = datetime(2025,4,28,20,49,19).timestamp()*1e9

tmin_period3c = tmax_period3b
tmax_period3c = datetime(2025, 4, 29, 17, 00, 00).timestamp() *1e9

tmin_period3d = tmax_period3c
tmax_period3d = datetime(2025, 5, 6, 9, 30,0).timestamp() *1e9

tmin_period3e = tmax_period3d
tmax_period3e = datetime(2025, 5, 6, 15, 20,0).timestamp() *1e9 

tmin_period3f = tmax_period3e
tmax_period3f = datetime(2025, 6, 2, 15, 0,0).timestamp() *1e9
tmin_period4 = tmax_period3f
tmax_period4 = datetime(2025, 6, 23, 18, 53, 0).timestamp() * 1e9

tmin_period5a = tmax_period4
tmax_period5a = datetime(2025,6,26,13,00,00).timestamp() *1e9

tmin_period5b = tmax_period5a
tmax_period5b = datetime(2025,6,26,21,40,00).timestamp() *1e9

tmin_period5c = tmax_period5b
tmax_period5c = tmax_run1.timestamp() * 1e9


# ---------------------------------------------------------------------------
# Per-sample calibration constants
# ---------------------------------------------------------------------------

mcbnb_offset_calib = -368.945
mcbnb_period_calib = 18.936

mchnl_offset_calib =  mcbnb_offset_calib
mchnl_period_calib = mcbnb_period_calib

offbeam_offset_calib = -525
offbeam_period_calib = 18.936


# ---------------------------------------------------------------------------
# Per-period calibration dicts
# ---------------------------------------------------------------------------

bad_period_dict = {
        "1b": [tmin_period1b, tmax_period1b]
        , "3c": [tmin_period3c, tmax_period3c]
        , "3e": [tmin_period3e, tmax_period3e]
        , "5b": [tmin_period5b, tmax_period5b]
     }

good_period_dict = { 
        "1ac": [tmin_period1a, tmax_period1c]
         ,  "1d": [tmin_period1d, tmax_period1d]
         , "rotation": [tmin_rotation, tmax_rotation]
         , "3a": [tmin_period3a, tmax_period3a]
         , "3b": [tmin_period3b, tmax_period3b] 
         , "3d": [tmin_period3d, tmax_period3d]
         , "3f": [tmin_period3f, tmax_period3f]
         , "4": [tmin_period4, tmax_period4]
         , "5ac": [tmin_period5a, tmax_period5c]
        }

pdict = {
        "1ac": np.float64(18.931)
         , "1d": np.float64(18.933)
         , "rotation": np.float64(18.938)
         , "3a": np.float64(18.936)
         , "3b": np.float64(18.937)
         , "3d": np.float64(18.936)
         , "3f": np.float64(18.936)
         , "4": np.float64(18.935)
         , "5ac": np.float64(18.937)
}

odict = { 
        "1ac": -525.165
         , "1d": -524.987
         , "rotation": -524.700
         , "3a": -524.858
         , "3b": -516.380
         , "3d": -524.780
         , "3f": -513.820
         , "4": -524.365
         , "5ac": -522.738
         }


# ---------------------------------------------------------------------------
# Bugfixes
# ---------------------------------------------------------------------------

def bugfix_mcbnb_bfm_flashtime(indf):

    mc_pds_cable_length = 0.135
    period = 18.936/1000
    indf[('slc', 'barycenterFM', 'flashTime', '', '', '')] = indf[('slc', 'barycenterFM', 'flashTime', '', '', '')] + mc_pds_cable_length + period*2
    return indf

def bugfix_mchnl_bfm_flashtime(indf):

    mc_pds_cable_length = 0.135
    indf[('slc', 'barycenterFM', 'flashTime', '', '', '')] = indf[('slc', 'barycenterFM', 'flashTime', '', '', '')] - mc_pds_cable_length
    return indf