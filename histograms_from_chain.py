#histograms_from_chain.py
# Import module
import numpy as np
import os
from matplotlib import pyplot as plt
import pandas as pd

# Folder containing Decompressed hdf5 files
#path = r"E:\vm_share\chain_data\RESreadable"
path = r"/media/sf_vm_share/chain_data/RESreadable"

# Change the directory
os.chdir(path)

S_4tot = []
sigma_phitot = []

binsize = 300

# Iterate through all files
for file in os.listdir():
    file_path = f"{path}/{file}"
    
    df = pd.read_pickle(file_path)
    
    S_4 = df['S_4']
    sigma_phi = df['sigma_phi']
    
    S_4tot = np.append(S_4tot, S_4)
    sigma_phitot = np.append(sigma_phitot,sigma_phi)
    
# Plot histograms
plt.figure(1)
plt.hist(S_4tot, bins=binsize)
plt.xscale('log')
plt.xlabel("Value")
plt.ylabel("Count")
plt.title('S_4 total')

plt.figure(2)
plt.hist(sigma_phitot, bins=binsize)
plt.xscale('log')
plt.xlabel("Value")
plt.ylabel("Count")
plt.title('sigma_phi total')
plt.show()

    
    
    