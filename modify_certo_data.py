#addon_ele_to_certo_data.py
import datetime as dt
import pandas as pd
import os
from skyfield.api import EarthSatellite,load, wgs84, Topos
from pymap3d import aer2ecef
import pytz

# Location of Certo
resolute_bay_lat_certo = 74.72955
resolute_bay_long_certo = 360-94.90576

certo_path = [r"E:\vm_share\Resolute\Data\2017pre_fix",
            r"E:\vm_share\Resolute\Data\2018pre_fix"]

save_path = [r"E:\vm_share\Resolute\Data\2017",
            r"E:\vm_share\Resolute\Data\2018"]

# Iterate through all files
for path_index,path in enumerate(certo_path):
    os.chdir(path)
    # Find how many .its files exist in directory
    its_files = 0
    for file in os.listdir():
        if file.endswith('.its'):
            its_files += 1
    current_file = 0
    for file in os.listdir():
        
        current_file += 1
        file_path = f"{path}\{file}"
        # read header
        with open(file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
        # Read how long the file is
        line_count = -7
        file_line = open(file_path, "r")
        for line in file_line:
            if line != "\n":
                line_count += 1
        file_line.close()
        
        # extract file start time and data rate from header
        split = header[2].split()
        file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
        file_start_time_aware = file_start_time.replace(tzinfo=pytz.UTC)
        data_rate = float(split[10])
        
        # get TLE from 4-5 lines of header
        lineelement1 = header[3]
        lineelement2 = header[4]
        
        # Creating a time array from the start time to propagate through a day in seconds
        utime = [file_start_time_aware+dt.timedelta(milliseconds=20*s) for s in range(line_count)]
        
        # I don't really understand what timescale is but everything in skyfield uses it
        ts = load.timescale()
        satellite = EarthSatellite(lineelement1, lineelement2, 'whatname',ts)
        rbo = Topos(resolute_bay_lat_certo, resolute_bay_long_certo)
        time = ts.from_datetimes(utime)
        el, az, rng = (satellite - rbo).at(time).altaz()
        
        xyz = aer2ecef(az.degrees, el.degrees, rng.m, resolute_bay_lat_certo, resolute_bay_long_certo, 145, ell=None, deg=True)
        
        df = pd.read_csv(file_path,skiprows=6,header=0)
        # Remove duplicate index column
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Convert data to a dataframe to write to file
        df['x_coor'] = xyz[0]
        df['y_coor'] = xyz[1]
        df['z_coor'] = xyz[2]
        
        # Remove unessisary/incorrect information from current dataframe
        del df["VHF_pow_interp"]
        del df["VHF_pha_interp"]
        del df["UHF_pow_interp"]
        del df["VHF_pow_d"]
        del df["VHF_pha_d"]
        del df["UHF_pow_d"]
        del df["VHF_pow_d_interp"]
        del df["VHF_pha_d_interp"]
        del df["UHF_pow_d_interp"]
        del df["VHF_S_4"]
        del df["UHF_S_4"]
        del df["VHF_sigma_phi"]
        del df["VHF_S_4_interp"]
        del df["UHF_S_4_interp"]
        del df["VHF_sigma_phi_interp"]
        del df["x_corr"]
        del df["y_corr"]
        del df["z_corr"]
        del df["x_vel"]
        del df["y_vel"]
        del df["z_vel"]
        
        completename = os.path.join(save_path[path_index], file)
        
        # Write dataframe to its file
        with open(completename, 'w') as txt_file:
            for headerline in header:
                txt_file.write(headerline)
            txt_file.write('EndOfHeader \n')
            df.to_csv(txt_file, sep=',', line_terminator='\n')
        
        print('Completed file ' + str(current_file) + ' of ' + str(its_files))
        