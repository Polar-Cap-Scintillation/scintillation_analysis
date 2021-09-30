#histograms_from_certo.py
# Import Module
import numpy as np
import os
from matplotlib import pyplot as plt

path = r"/media/sf_VirtualboxShare/Resolute/Data/2018"
#path = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2018"

# Change the directory
os.chdir(path)

VHF_S_4tot = []
UHF_S_4tot = []
VHF_sigma_phitot = []

binsize = 50

# Iterate through all files
for file in os.listdir():
    file_path = f"{path}/{file}"

    # read header
    with open(file_path) as fileheader:
        header = [next(fileheader) for x in range(5)]
    
    # extract file start time and data rate from header
    split = header[2].split()
    filestarttime = split[4] + split[5]
    
    # read data from *.its file
    # Order is index,VHF_pow,VHF_pha,UHF_pow,UHF_pha,VHF_pow_d,VHF_pha_d,UHF_pow_d,UHF_pha_d,
    # VHF_S_4,UHF_S_4,VHF_sigma_phi,UHF_sigma_phi,x_corr,y_corr,z_corr,x_vel,y_vel,z_vel
    _, _, _, _, _, _, _, _, _, VHF_S_4, UHF_S_4, VHF_sigma_phi, _, \
        _, _, _, _, _, _, = np.genfromtxt(file_path,skip_header=8,unpack=True, delimiter = ",")
    
    VHF_S_4tot = np.append(VHF_S_4tot, VHF_S_4)
    UHF_S_4tot = np.append(UHF_S_4tot, UHF_S_4)
    VHF_sigma_phitot = np.append(VHF_sigma_phitot, VHF_sigma_phi)
    
    
# Plot histograms
plt.figure(1)
plt.hist(VHF_S_4tot, bins=binsize,range=[0,50])  
plt.xscale('log')
plt.xlabel("Value")
plt.ylabel("Count")
plt.title('VHF S_4')

plt.figure(2)
plt.hist(UHF_S_4tot, bins=binsize,range=[0,50])
plt.xscale('log')
plt.xlabel("Value")
plt.ylabel("Count")
plt.title('UHF S_4')

plt.figure(3)
plt.hist(VHF_sigma_phitot, bins=binsize,range=[0,50])
plt.xscale('log')
plt.xlabel("Value")
plt.ylabel("Count")
plt.title('VHF_sigma_phi')

plt.show()

    