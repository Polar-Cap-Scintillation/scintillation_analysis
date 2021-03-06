"""
comparing speed of bra-ket definition of coefficent of varience
and standard deviation to numpy bulit in functions
along with new numpy window sliding view function
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
    
    s4 = lambda x: np.std(x, ddof=0) / abs(np.mean(x))
    
    return np.array([np.nan]*hw+[s4(power[i-hw:i+hw]) for i in range(hw,len(power)-hw)]+[np.nan]*hw)

def bulits4sliding(utime, power, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points
    
    rw = np.lib.stride_tricks.sliding_window_view(power,hw*2)
    rw = np.delete(rw,len(rw)-1,0) # Delete last row for accurate results
    
    return np.concatenate(([np.nan]*hw,np.std(rw,axis=1,ddof=0) / abs(np.mean(rw,axis=1)), [np.nan]*hw), axis=None)


def braketsp(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    sigp = lambda x: np.sqrt(np.nanmean(x**2)-np.nanmean(x)**2)

    return np.array([np.nan]*hw+[sigp(phase[i-hw:i+hw]) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)

def bulitsp(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points

    return np.array([np.nan]*hw+[np.std(phase[i-hw:i+hw], ddof=0) for i in range(hw,len(phase)-hw)]+[np.nan]*hw)

def bulitspsliding(utime, phase, window):
    datarate = 1./np.mean(np.diff(utime))
    hw = int(window/2.*datarate)    # half window in points
    
    rw = np.lib.stride_tricks.sliding_window_view(phase,hw*2)
    rw = np.delete(rw,len(rw)-1,0) # Delete last row for accurate results
    
    return np.concatenate(([np.nan]*hw, np.std(rw, axis=1, ddof=0), [np.nan]*hw), axis=None)

# Made this to check if I was doing np.std correctly
def error(x1,x2):
    err = 200*np.abs(x1-x2)/(x1+x2)
    if np.nanmax(err) == 0:
        return True
    return False
    
# Input the detrended power/phase
def timediff(utime,power,phase,window):
    
    print('----s4 comparison----')
    print('braket method')
    tic()
    brs4 = brakets4(utime,power,window)
    toc()
    print('built in numpy method')
    tic()
    bus4 = bulits4(utime,power,window)
    toc()
    print('built in numpy with window sliding method')
    tic()
    bus4s = bulits4sliding(utime,power,window)
    toc()
    
    print('----sigmaphi comparison----')
    print('braket method')
    tic()
    brsp = braketsp(utime,phase,window)
    toc()
    print('built in numpy method')
    tic()
    busp = bulitsp(utime,phase,window)
    toc()
    print('built in numpy with window sliding method')
    tic()
    busps = bulitspsliding(utime,phase,window)
    toc()
    
    if error(brs4, bus4):
        print('Built in numpy does not match the original braket method for S4')
    if error(brs4, bus4s):
        print('Built in numpy with window sliding does not match the original braket method for S4')
    if error(brsp, busp):
        print('Built in numpy does not match the original braket method for sigma phi')
    if error(brsp, busps):
        print('Built in numpy with window sliding does not match the original braket method for sigma phi')
        
    
    return None
    
    