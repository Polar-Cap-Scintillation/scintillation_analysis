"""
comparing speed of bra-ket definition of coefficent of varience
and standard deviation to numpy bulit in functions
"""

import numpy as np
import time

# Stole this idea from https://stackoverflow.com/questions/5849800/what-is-the-python-equivalent-of-matlabs-tic-and-toc-functions
def TicTocGenerator():
    # Generator that returns time differences
    ti = 0           # initial time
    tf = time.time() # final time
    while True:
        ti = tf
        tf = time.time()
        yield tf-ti # returns the time difference

TicToc = TicTocGenerator() # create an instance of the TicTocGen generator

# This will be the main function through which we define both tic() and toc()
def toc(tempBool=True):
    # Prints the time difference yielded by generator instance TicToc
    tempTimeInterval = next(TicToc)
    if tempBool:
        print( "Elapsed time: %f seconds.\n" %tempTimeInterval )

def tic():
    # Records a time in TicToc, marks the beginning of a time interval
    toc(False)
    
    
def brakets4(utime, power, window):
    
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    s4 = lambda x: np.sqrt((np.nanmean(x**2)-np.nanmean(x)**2)/np.nanmean(x)**2)

    return np.array([np.nan]*hw+[s4(power[i-hw:i+hw]) for i in range(hw,len(power)-hw)]+[np.nan]*hw)

def bulits4(utime, power, window):
    
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points
    
    s4 = lambda x: np.std(x, ddof=0) / np.mean(x)
    
    return np.array([np.nan]*hw+[s4(power[i-hw:i+hw]) for i in range(hw,len(power)-hw)]+[np.nan]*hw)

def braketsp(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    sigp = lambda x: np.sqrt(np.nanmean(x**2)-np.nanmean(x)**2)

    return np.array([np.nan]*hw+[sigp(phase[i-hw:i+hw]) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)

def bulitsp(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    return np.array([np.nan]*hw+[np.std(phase[i-hw:i+hw], ddof=0) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)

# Made this to check if I was doing np.std correctly
def error(x1,x2):
    return 200*np.abs(x1-x2)/(x1+x2)
    

def timediff(utime,power,phase,window):
    
    tic()
    brakets4(utime,power,window)
    toc()
    
    tic()
    bulits4(utime,power,window)
    toc()
    
    tic()
    braketsp(utime,phase,window)
    toc()
    
    tic()
    bulitsp(utime,phase,window)
    toc()
    
    return None
    
    