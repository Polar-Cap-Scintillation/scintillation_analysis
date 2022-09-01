import h5py
import numpy as np
import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as mdates
import os
import pandas as pd

path = r'E:\vm_share\risr\data_files'
conjunctions_df = pd.read_csv(r'E:\vm_share\risr\conjunctions_start_times.csv')

os.chdir(path)
file_number = 0
for file in os.listdir():
    file_number+=1
    myFmt = mdates.DateFormatter('%H:%M:%S')
    # Read attributes from hdf5 file
    with h5py.File(file, 'r') as h5:
        # find maximum elevation beam
        bc = h5['BeamCodes'][:]
        bidx = np.argmax(bc[:,2])
        
        # read in data from max elevation beam
        utime = h5['Time/UnixTime'][:]
        alt = h5['FittedParams/Altitude'][bidx,:]
        dens = h5['FittedParams/Ne'][:,bidx,:]
    
    print(utime.shape, alt.shape, dens.shape)
    
    utimedt = [dt.datetime.utcfromtimestamp(utime[j,0]) for j in range(0,len(utime))]
    time_of_intrest_start = list()
    for conjunction in range(len(conjunctions_df)):
        if file_number == conjunctions_df.loc[conjunction,'file']:
            
            time_of_intrest_start.append(dt.datetime.strptime(str(conjunctions_df.loc[conjunction,'file_start_time']),'%Y%m%d%H%M%S') + dt.timedelta(milliseconds=20*int(conjunctions_df.loc[conjunction,'start_index'])))
            
    # time_of_intrest_end = dt.datetime.strptime('20170718133825','%Y%m%d%H%M%S') + dt.timedelta(milliseconds=int(20*12697))
    fig1 = plt.figure(figsize=(10, 4), dpi=80)
    ax1 = plt.subplot2grid((1,1), (0,0))
    fig1.tight_layout()
    
    # Setting the length of the axis for all plots
    ax1.set(xlabel='Time', ylabel='Density [$m^{-3}$]', title='Electron density at ' + str(utimedt[0]))
    
    ax1.xaxis.set_major_formatter(myFmt)
    
    C = ax1.pcolormesh(utimedt, alt[np.isfinite(alt)], dens[:,np.isfinite(alt)].T, vmin=0, vmax=5.e11)
    fig1.colorbar(C)
    
    # only one line may be specified; full height
    for vertical_line in time_of_intrest_start:
        ax1.axvline(x = vertical_line, color = 'r', label = vertical_line)
    ax1.legend()
    plt.show()
    
    plt.close()
    
    