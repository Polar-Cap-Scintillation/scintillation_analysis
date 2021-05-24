# detrend.py
# Functions to detrend the power and phase timeseries

import numpy as np
from scipy.signal import butter, filtfilt, detrend

def power_detrend(utime, power):
    datarate = 1./np.mean(np.diff(utime))
    cutoff=0.1

    b, a = butter(6,cutoff/(0.5*datarate))
    y = filtfilt(b,a,power)
    power_detrend = power/y
    return power_detrend


def phase_detrend(utime, phase):
    # get total length of phase time series
    LP = len(phase)

    # removing third order polynomial trend
    x = np.arange(LP)
    p = np.poly1d(np.polyfit(x,phase,3))
    p1 = phase-p(x)

    # detrend
    p2 = detrend(p1) # This does almost nothing?

    # form Butterworth filter
    dfreq = 1./(utime[-1]-utime[0])
    cutoff = 0.1
    order = 6
    freq = -LP/2.*dfreq+np.arange(LP)*dfreq
    butterhi = 1.0-1./np.sqrt(1 + (freq/cutoff)**(2*order))

    # fft of phase data?
    phase_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(p2)))
    # inverse fft of phase multiplied by the Butterworth filter
    phase_detrend = np.fft.fftshift(np.fft.ifft(np.fft.ifftshift(phase_fft*butterhi)))
    return np.real(phase_detrend)
