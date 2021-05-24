# scint_index.py
# Basic functions to caluclate scintillation indices, S_4 (power) and sigma_phi (phase)

import numpy as np

def S_4(utime, power, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    s4 = lambda x: np.sqrt((np.nanmean(x**2)-np.nanmean(x)**2)/np.nanmean(x)**2)

    return np.array([np.nan]*hw+[s4(power[i-hw:i+hw]) for i in range(hw,len(power)-hw)]+[np.nan]*hw)


def sigma_phi(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    sigp = lambda x: np.sqrt(np.nanmean(x**2)-np.nanmean(x)**2)

    return np.array([np.nan]*hw+[sigp(phase[i-hw:i+hw]) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)
