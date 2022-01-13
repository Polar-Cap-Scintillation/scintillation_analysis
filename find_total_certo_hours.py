#find_total_certo_hours.py
# Import Module
import numpy as np
import os
from matplotlib import pyplot as plt
import datetime as dt
# Used for finding the row index of the unessisary data at the end of .pro files
# Taken from: https://stackoverflow.com/questions/15718068/search-file-and-find-exact-match-and-print-line
def lines_that_contain(string, fp):
    return [index for index, line in enumerate(fp) if string in line]

propath = [r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\2017",
            r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\2018"]
datapath = [r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2017",
            r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2018"]

# Find how many .its files exist in directory
its_files = 0
for paths in datapath:
    os.chdir(paths)
    for file in os.listdir():
        if file.endswith('.its'):
            its_files += 1

indextot = 0

# Iterate through all files
current_file = 0
i = 0
for paths in datapath:
    os.chdir(paths)
    for file in os.listdir():
        data_file_path = f"{paths}/{file}"
        # profile = file[3:-4] + '.pro'
        # pro_file_path = f"{propath[i]}/{profile}"
        if file.endswith(".its"):
            current_file += 1
            # Some files lack data and need to be thrown out
            try:
                # Getting data from the data files
                # Order is index,VHF_pow,VHF_pha,UHF_pow,VHF_pow_i,VHF_pha_i,UHF_pow_i,
                # VHF_pow_d,VHF_pha_d,UHF_pow_d,VHF_pow_d_i,VHF_pha_d_i,UHF_pow_d_i,
                # VHF_S_4,UHF_S_4,VHF_sigma_phi,VHF_S_4_i,UHF_S_4_i,VHF_sigma_phi_i,
                # x_corr,y_corr,z_corr,x_vel,y_vel,z_vel
                
                index, _, _, _, _, _, _, \
                    _, _, _, _, _, _, \
                    _, _, _, _, _, _, \
                    _, _, _, _, _, _, = np.genfromtxt(data_file_path,skip_header=8,unpack=True, delimiter = ",")
                
                indextot = indextot+index[-1]
                
            except ValueError:
                # Do nothing
                pass
            print('Completed file ' + str(current_file) + ' of ' + str(its_files))
    i+=1

timetotal = indextot*0.02

print(str(dt.timedelta(seconds=timetotal)))

    