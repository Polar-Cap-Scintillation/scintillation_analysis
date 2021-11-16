# parse_certo.py
import numpy as np
import datetime as dt
from sgp4.api import Satrec # pip install sgp4
import pandas as pd
from detrend import power_detrend, phase_detrend
from scint_index import S_4, sigma_phi
import os
# CERTO data
certo_data = {}

# Used for finding the row index of the unessisary data at the end of .pro files
# Taken from: https://stackoverflow.com/questions/15718068/search-file-and-find-exact-match-and-print-line
def lines_that_contain(string, fp):
    return [index for index, line in enumerate(fp) if string in line]

def parse_certo_its_file(file_path, pro_file_path):

    # Some file lack data and need to be thrown out
    try:
        # read header
        with open(file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
    
        # extract file start time and data rate from header
        split = header[2].split()
        file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
        data_rate = float(split[10])
        
        # get TLE from 4-5 lines of header
        lineelement1 = header[3]
        lineelement2 = header[4]
    
        # read data from *.its file
        VHFI, VHFQ, UHFI, UHFQ, _, _, _ = np.loadtxt(file_path,skiprows=8,unpack=True)
        
        
        # generate time array
        utime = np.array([(file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()+t/data_rate for t in range(len(VHFI))])
        
        VHF_power = VHFI**2+VHFQ**2
        VHF_phase = np.unwrap(np.arctan2(VHFQ,VHFI))
        UHF_power = UHFI**2+UHFQ**2
        
        with open(pro_file_path, 'r') as fp:
            end_line = lines_that_contain('RMS phase',fp)[-1]-9
        
        # read header
        with open(pro_file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
        # extract file start time and data rate from header
        split = header[2].split()
        data_rate = float(split[10])
        
        # Getting data from the flag files
        _, _, UHF_pow_f, VHF_pow_f, phasef, _, _, _, _, _, _ = np.loadtxt(pro_file_path,skiprows=9,unpack=True, max_rows=end_line)
        
        VHF_pow_f = np.repeat(VHF_pow_f,data_rate)
        UHF_pow_f = np.repeat(UHF_pow_f,data_rate)
        phasef = np.repeat(phasef,data_rate)
        
        time = np.arange(len(UHF_pow_f))
        
        VHF_pow_interp = np.copy(VHF_power[0:len(UHF_pow_f)])
        UHF_pow_interp = np.copy(UHF_power[0:len(UHF_pow_f)])
        VHF_pha_interp = np.copy(VHF_phase[0:len(UHF_pow_f)])
        
        VHF_pow_interp[VHF_pow_f!=0] = np.interp(time[VHF_pow_f!=0], time[VHF_pow_f==0], VHF_pow_interp[VHF_pow_f==0],right=np.nan)
        UHF_pow_interp[UHF_pow_f!=0] = np.interp(time[UHF_pow_f!=0], time[UHF_pow_f==0], UHF_pow_interp[UHF_pow_f==0],right=np.nan)
        VHF_pha_interp[phasef!=0] = np.interp(time[phasef!=0], time[phasef==0], VHF_pha_interp[phasef==0],right=np.nan)
        
        # Removing nan values
        VHF_pow_interp = VHF_pow_interp[~np.isnan(VHF_pow_interp)]
        UHF_pow_interp = UHF_pow_interp[~np.isnan(UHF_pow_interp)]
        VHF_pha_interp = VHF_pha_interp[~np.isnan(VHF_pha_interp)]
    
        # Set window to value between 10-60
        window = 10
    
        # get information on satellite positional data from sgp4
        satellite = Satrec.twoline2rv(lineelement1, lineelement2)
        
        # Convert utime from utc seconds to Timestamp to convert to julian date
        # Conversion may be a few leap seconds off
        jd = utime / 86400.0 + 2440587.5
        
        # sgp4 needs two separate variables for julian time
        fr = jd % 1
        jd = np.array([int(jds) for jds in jd])
        
        # Preset list for calculation
        # e will be a non-zero error code if the satellite position could not be computed for the given date.
        e, r, v = satellite.sgp4_array(jd,fr)
        
        # Extracting the x, y, and z positions for creating dataframe
        xcorr = [value[0] for value in r]
        ycorr = [value[1] for value in r]
        zcorr = [value[2] for value in r]
        
        # Extracting the x, y, and z velocities for creating dataframe
        xvel = [value[0] for value in v]
        yvel = [value[1] for value in v]
        zvel = [value[2] for value in v]
        
        # Calculate the detrend
        VHF_power_detrend = power_detrend(utime,VHF_power)
        UHF_power_detrend = power_detrend(utime,UHF_power)
        VHF_phase_detrend = phase_detrend(utime,VHF_phase)
        
        # Calculate S_4 and sigma_phi for VHF and UHF
        VHF_S_4 = S_4(utime, VHF_power_detrend,window)
        UHF_S_4 = S_4(utime, UHF_power_detrend,window)
        VHF_sigma_phi = sigma_phi(utime, VHF_phase_detrend,window)
        
        # Calculate the linear interpolated detrend
        VHF_power_detrend_interp = power_detrend(utime,VHF_pow_interp)
        UHF_power_detrend_interp = power_detrend(utime,UHF_pow_interp)
        VHF_phase_detrend_interp = phase_detrend(utime,VHF_pha_interp)
        
        # Calculate the linear interpolated S_4 and sigma_phi
        VHF_S_4_interp = S_4(utime, VHF_power_detrend_interp,window)
        UHF_S_4_interp = S_4(utime, UHF_power_detrend_interp,window)
        VHF_sigma_phi_interp = sigma_phi(utime, VHF_phase_detrend_interp,window)
        
    except ValueError:
        return None, None
    
    # Convert data to a datafrom to write to file
    d = {'VHF_pow' : VHF_power, 'VHF_pha' : VHF_phase, 'UHF_pow' : UHF_power,
        'VHF_pow_interp' : VHF_pow_interp, 'VHF_pha_interp' : VHF_pha_interp, 
        'UHF_pow_interp' : UHF_pow_interp, 'VHF_pow_d' : VHF_power_detrend, 
        'VHF_pha_d' : VHF_phase_detrend, 'UHF_pow_d' : UHF_power_detrend, 
        'VHF_pow_d_interp' : VHF_power_detrend_interp, 'VHF_pha_d_interp' : VHF_phase_detrend_interp,
        'UHF_pow_d_interp' : UHF_power_detrend_interp, 'VHF_S_4' : VHF_S_4, 
        'UHF_S_4' : UHF_S_4, 'VHF_sigma_phi' : VHF_sigma_phi, 'VHF_S_4_interp' : VHF_S_4_interp, 
        'UHF_S_4_interp' : UHF_S_4_interp, 'VHF_sigma_phi_interp' : VHF_sigma_phi_interp, 
        'x_corr' : xcorr, 'y_corr' : ycorr, 'z_corr' : zcorr, 'x_vel' : xvel, 
        'y_vel' : yvel, 'z_vel' : zvel}
    df = pd.DataFrame.from_dict(d, orient='index')
    df = df.transpose()
    
    return df, header


def main():
    # Folder containing the certo data files
    path = r"/media/sf_VirtualboxShare/Resolute/2018"
    #path = r"C:\Users\TateColby\Desktop\Resolute\2018"
    # Save Path
    save_path = r"/media/sf_VirtualboxShare/Resolute/Data/2018"
    #save_path = r"C:\Users\TateColby\Desktop\Calctestpy\scintillation_analysis-main\Updatedfiles\Resolute\2018"
    
    # Change the directory
    os.chdir(path)
    
    # Find how many .its files exist in directory
    its_files = 0
    for file in os.listdir():
        if file.endswith('.its'):
            its_files += 1
    
    # Iterate through all files
    current_file = 0
    for file in os.listdir():
        # Check whether file is in .its format or not
        if file.endswith(".its"):
            current_file += 1
            file_path = f"{path}/{file}"
            profile = file[0:-4] + '.pro'
            pro_file_path = f"{path}/{profile}"
            df, header = parse_certo_its_file(file_path,pro_file_path)
            if header != None:
                # Write new data to a file
                # complete_name = os.path.join(save_path, 'picke' + file[0:-4] + '.pkl')
                # df.to_pickle(complete_name)
                
                completename = os.path.join(save_path, 'new' + file)
                
                # Change this to look better
                with open(completename, 'w') as txt_file:
                    for headerline in header:
                        txt_file.write(headerline)
                    txt_file.write('EndOfHeader \n')
                    df.to_csv(txt_file, sep=',')
                return
            print('Completed file ' + str(current_file) + ' of ' + str(its_files))
        
if __name__=='__main__':
    main()
    