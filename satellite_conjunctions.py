#satellite_conjunctions.py
import numpy as np
import pandas as pd
import os
from itertools import groupby
from operator import itemgetter
from pymap3d import ecef2aer

def haversine(theta):
    return (1-np.cos(theta))/2

# certo_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2017"
certo_path = [r"/media/sf_vm_share/Resolute/Data/2017",
              r"/media/sf_vm_share/Resolute/Data/2018"]

# chain_path = r"E:\vm_share\chain_data\RESreadable"
chain_path = r"/media/sf_vm_share/chain_data/RESreadable"

# save_path = r"E:\vm_share\chain_data\conjunctions"
save_path = r"/media/sf_vm_share/conjunctions"

# Resolute Bay position
resolute_bay_lat_certo = 74.72955
resolute_bay_long_certo = 360-94.90576
resolute_bay_lat_chain = 74.746627
resolute_bay_long_chain = 264.997469

# Cutoff angle (radians)
cutoff = np.array([1,2,4,5])*5*np.pi/180

# Find how many .its files exist in directory
# its_files = 0
# for paths in certo_path:
#     os.chdir(paths)
#     for file in os.listdir():
#         if file.endswith('.its'):
#             its_files += 1

#Iterate through all cufoff angles
for cut in cutoff:
    save_file = 'cutoff' + str(int(cut*180/np.pi)) + 'conjunctions.txt'
    # Iterate through all files
    current_file = 0
    for paths in certo_path:
        os.chdir(paths)
        for file in os.listdir():
            data_file_path = f"{paths}/{file}"
            
            current_file += 1
            # Some files lack data and need to be thrown out
            try:
                
                # Getting data from the data files
                # Order is index,VHF_pow,VHF_pha,UHF_pow,VHF_pow_i,VHF_pha_i,UHF_pow_i,
                # VHF_pow_d,VHF_pha_d,UHF_pow_d,VHF_pow_d_i,VHF_pha_d_i,UHF_pow_d_i,
                # VHF_S_4,UHF_S_4,VHF_sigma_phi,VHF_S_4_i,UHF_S_4_i,VHF_sigma_phi_i,
                # x_corr,y_corr,z_corr,x_vel,y_vel,z_vel
                
                _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, \
                    x, y, z, xv, yv, zv, = np.genfromtxt(data_file_path,skip_header=8,unpack=True, delimiter = ",")
                
                x_cor = {'certo':x}
                y_cor = {'certo':y}
                z_cor = {'certo':z}
                
                # Find matching CHAIN data to CERTO data
                os.chdir(chain_path)
                for chain_file in os.listdir():
                    if chain_file[3:-9] == file[3:-5]:
                        chain_file_path = f"{chain_path}/{chain_file}"
                        df = pd.read_pickle(chain_file_path)
                        chain_prn = chain_file[17:22]
                        
                        # Using this to match the length of the CERTO and CHAIN datasets
                        # https://stackoverflow.com/questions/63937664/match-length-of-arrays-in-python
                        m = min(len(x_cor['certo']), len(np.array(df['x_corr'])))
                        x_cor['certo'] = x_cor['certo'][:m]
                        x_cor[chain_prn] = np.array(df['x_corr'][:m])
                        
                        m = min(len(y_cor['certo']), len(np.array(df['y_corr'])))
                        y_cor['certo'] = y_cor['certo'][:m]
                        y_cor[chain_prn] = np.array(df['y_corr'][:m])
                        
                        m = min(len(z_cor['certo']), len(np.array(df['z_corr'])))
                        z_cor['certo'] = z_cor['certo'][:m]
                        z_cor[chain_prn] = np.array(df['z_corr'][:m])
                
                # Calculate the azimuth, elevatoin, and slant range from Resolute Bay
                azi_ele = {}
                hav = {}
                theta = {}
                azi_ele['certo'] = np.radians(ecef2aer(x_cor['certo']*100, y_cor['certo']*100, z_cor['certo']*100, resolute_bay_lat_certo, resolute_bay_long_certo, 145, deg=True))
                for sat in x_cor:
                    if sat != 'certo':
                        # Calculate he azimuth with input degrees and output radians
                        azi_ele[sat] = np.radians(ecef2aer(x_cor[sat]*100, y_cor[sat]*100, z_cor[sat]*100, resolute_bay_lat_chain, resolute_bay_long_chain, 0, deg=True))
                        
                        # Calculate the angular separation between CERTO and CHAIN satellites with the haversine formula
                        hav[sat] = haversine(azi_ele[sat][1]-azi_ele['certo'][1])+np.cos(azi_ele['certo'][1])*np.cos(azi_ele[sat][1])*haversine(azi_ele[sat][0]-azi_ele['certo'][0])
                        theta[sat] = 2*np.arcsin(np.sqrt(hav[sat]))
                        
                        # Finding where all the points of intrest are
                        notable_times = [i for i,v in enumerate(theta[sat]) if v < (cut)]
                        
                        # Taken from: https://stackoverflow.com/questions/2154249/identify-groups-of-continuous-numbers-in-a-list
                        # This splits up notable_times into the begining and end indexes of continuous time ranges
                        ranges = []
                        for k,g in groupby(enumerate(notable_times),lambda x:x[0]-x[1]):
                            group = (map(itemgetter(1),g))
                            group = list(map(int,group))
                            ranges.append((group[0],group[-1]))
                        
                        # Save to file iff ranges is not empty
                        if ranges:
                            os.chdir(save_path)
                            with open(save_file,'a') as myfile:
                                myfile.write(str(file[3:-5]) + ' ' + sat + '  Ranges: ' + str(ranges) + '\n')
                        # print(sat + ' avg: ' + str(np.average(theta[sat])) + ' max: ' + str(np.max(theta[sat])) + ' min: ' + str(np.min(theta[sat])) + ' Ranges: ' + str(ranges))
                
            except ValueError:
                # Do nothing
                pass
    
            # print('Completed file ' + str(current_file) + ' of ' + str(its_files))
            
            # Change back to certo path for loop. I'm unsure if this is necessary
            os.chdir(paths)
            
    print('Completed ' + str(int(cut*180/np.pi)))
        