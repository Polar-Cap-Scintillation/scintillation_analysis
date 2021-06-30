# parse_certo.py
import numpy as np
import datetime as dt
from sgp4.api import Satrec # pip install sgp4
import pandas as pd
import math as ma
from detrend import power_detrend, phase_detrend
from scint_index import S_4, sigma_phi
# Import Module
import os
# CERTO data
certo_data = {}

# Folder Path
# Change to your own file location
path = r"C:\Users\TateColby\Desktop\Eureka\2017"

# Save Path
# Change to where you want to save the file to
savepath = r"C:\Users\TateColby\Desktop\Calctestpy\scintillation_analysis-main\Updatedfiles"

# Change the directory
os.chdir(path)

# Set window to value between 10-60
window = 10

# iterate through all file
for file in os.listdir():
    # Check whether file is in its format or not
    if file.endswith(".its"):
        file_path = f"{path}\{file}"

        # read header
        with open(file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
        
        # extract file start time and data rate from header
        split = header[2].split()
        filestarttime = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
        datarate = float(split[10])
        
        # get TLE from 4-5 lines of header
        lineelement1 = header[3]
        lineelement2 = header[4]
        
        # read data from *.its file
        VHFI, VHFQ, UHFI, UHFQ, _, _, _ = np.loadtxt(file_path,skiprows=8,unpack=True)
        
        # generate time array
        utime = np.array([(filestarttime-dt.datetime.utcfromtimestamp(0)).total_seconds()+t/datarate for t in range(len(VHFI))])
        
        VHF_power = VHFI**2+VHFQ**2
        VHF_phase = np.unwrap(np.arctan2(VHFQ,VHFI))
        UHF_power = UHFI**2+UHFQ**2
        UHF_phase = np.unwrap(np.arctan2(UHFQ,UHFI))
        
        # get information on satellite positional data from sgp4
        satellite = Satrec.twoline2rv(lineelement1, lineelement2)
        
        # Convert utime from utc seconds to Timestamp to convert to julian date
        # Conversion may be a few leap seconds off
        jd = utime / 86400.0 + 2440587.5
        
        # sgp4 needs two separate variables for julian time
        fr = jd % 1
        jd = [ma.trunc(jds) for jds in jd]
        
        # Preset list for calculation
        # e will be a non-zero error code if the satellite position could not be computed for the given date.
        e = [None] * len(jd)
        r = [[None,None,None]] * len(jd)
        v = [[None,None,None]] * len(jd)
        
        # Calculate true equator mean equinox position and velocity
        for i in range(len(jd)):
            e[i],r[i],v[i] = satellite.sgp4(jd[i],fr[i])
        
        # Extracting the x, y, and z positions for creating dataframe
        xcorr = [value[0] for value in r]
        ycorr = [value[1] for value in r]
        zcorr = [value[2] for value in r]
        
        # Extracting the x, y, and z velocities for creating dataframe
        xvel = [value[0] for value in v]
        yvel = [value[1] for value in v]
        zvel = [value[2] for value in v]
        
        #print(r)  # True Equator Mean Equinox position (km)
        #print(v)  # True Equator Mean Equinox velocity (km/s)
        print('Thinking time')
        # Calculate the detrend
        VHF_power_detrend = power_detrend(utime,VHF_power)
        UHF_power_detrend = power_detrend(utime,UHF_power)
        VHF_phase_detrend = phase_detrend(utime,VHF_phase)
        UHF_phase_detrend = phase_detrend(utime,UHF_power)
        
        # Calculate S_4 and sigma_phi for VHF and UHF
        
        VHF_S_4 = S_4(utime, VHF_power,window)
        UHF_S_4 = S_4(utime, UHF_power,window)
        VHF_sigma_phi = sigma_phi(utime, VHF_phase,window)
        UHF_sigma_phi = sigma_phi(utime, UHF_phase,window)
        
        # Convert data to a datafrom to write to file
        df = pd.DataFrame({'VHF_pow' : VHF_power, 'VHF_pha' : VHF_phase, 'UHF_pow' : UHF_power,
                           'UHF_pha' : UHF_phase, 'VHF_pow_d' : VHF_power_detrend, 'VHF_pha_d' : VHF_phase_detrend,
                           'UHF_pow_d' : UHF_power_detrend, 'UHF_pha_d' : UHF_phase_detrend, 'VHF_S_4' : VHF_S_4, 
                           'UHF_S_4' : UHF_S_4, 'VHF_sigma_phi' : VHF_sigma_phi, 'UHF_sigma_phi' : UHF_sigma_phi,
                           'x_corr' : xcorr, 'y_corr' : ycorr, 'z_corr' : zcorr, 'x_vel' : xvel, 
                           'y_vel' : yvel, 'z_vel' : zvel})
        
        # Write new data to a file
        completename = os.path.join(savepath, 'new' + file)
        
        # Change this to look better
        with open(completename, 'w') as txt_file:
            for headerline in header:
                txt_file.write(headerline)
            txt_file.write('EndOfHeader \n')
            df.to_csv(txt_file, sep='\t')
            print('I made it')
