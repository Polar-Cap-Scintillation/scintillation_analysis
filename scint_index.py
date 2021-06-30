# scint_index.py
# Basic functions to caluclate scintillation indices, S_4 (power) and sigma_phi (phase)

import numpy as np

def S_4(utime, power, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    s4 = lambda x: np.std(x, ddof=0) / np.mean(x)
    
    return np.array([np.nan]*hw+[s4(power[i-hw:i+hw]) for i in range(hw,len(power)-hw)]+[np.nan]*hw)


def sigma_phi(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    return np.array([np.nan]*hw+[np.std(phase[i-hw:i+hw], ddof=0) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)
