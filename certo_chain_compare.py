#certo_chain_compare.py
import numpy as np
import os
import pandas as pd
from matplotlib import pyplot as plt

cutoff_file = r"E:\vm_share\conjunctions\cutoff15conjunctions.csv"
# cutoff_file = r"/media/sf_vm_share/conjunctions/cutoff15conjunctions.csv"

certo_path = [r"E:\vm_share\Resolute\Data\2017",
            r"E:\vm_share\Resolute\Data\2018"]
# certo_path = [r"/media/sf_VirtualboxShare/Resolute/Data/2017",
#             r"/media/sf_VirtualboxShare/Resolute/Data/2018"]

chain_path = r"E:\vm_share\chain_data\RESreadable"
#chain_path = r"/media/sf_vm_share/chain_data/RESreadable"

# Define the cutoff file times
df_cut = pd.read_csv(cutoff_file)

for i in range(len(df_cut['time'])):
    for paths in certo_path:
        os.chdir(paths)
        for file in os.listdir():
            
            if str(df_cut['time'][i]) == file[3:-5]:
                data_file_path = f"{paths}\{file}"
                
                # Some files lack data and need to be thrown out
                try:
                    # Getting data from the data files
                    # Order is index,VHF_pow,VHF_pha,UHF_pow,VHF_pow_i,VHF_pha_i,UHF_pow_i,
                    # VHF_pow_d,VHF_pha_d,UHF_pow_d,VHF_pow_d_i,VHF_pha_d_i,UHF_pow_d_i,
                    # VHF_S_4,UHF_S_4,VHF_sigma_phi,VHF_S_4_i,UHF_S_4_i,VHF_sigma_phi_i,
                    # x_corr,y_corr,z_corr,x_vel,y_vel,z_vel
                    
                    _, VHF_pow_d, VHF_pha, UHF_pow, _, _, _, \
                        VHF_pow_d, VHF_pha_d, UHF_pow_d, _, _, _, \
                        _, _, _, _, _, _, \
                        _, _, _, _, _, _, = np.genfromtxt(data_file_path,skip_header=8,unpack=True, delimiter = ",")
                    
                    # Filtering out the cutoff times
                    power = {'certo_VHF': VHF_pow_d[df_cut['start'][i]:df_cut['end'][i]], 'certo_UHF': UHF_pow_d[df_cut['start'][i]:df_cut['end'][i]]}
                    phase = {'certo':VHF_pha_d[df_cut['start'][i]:df_cut['end'][i]]}
                    
                    # Find matching CHAIN data to CERTO data
                    os.chdir(chain_path)
                    for chain_file in os.listdir():
                        if chain_file[3:-9] == file[3:-5] and chain_file[-9:-4] == df_cut['sat'][i]:
                            chain_file_path = f"{chain_path}/{chain_file}"
                            df_chain = pd.read_pickle(chain_file_path)
                            chain_prn = df_cut['sat'][i]
                            
                            # Using this to match the length of the CERTO and CHAIN datasets
                            # https://stackoverflow.com/questions/63937664/match-length-of-arrays-in-python
                            m = min(len(power['certo_VHF']), len(np.array(df_chain['power_d'][df_cut['start'][i]:df_cut['end'][i]])))
                            power['certo_VHF'] = power['certo_VHF'][:m]
                            power[chain_prn] = np.array(df_chain['power_d'][:m])
                            
                            m = min(len(power['certo_UHF']), len(np.array(df_chain['power_d'][df_cut['start'][i]:df_cut['end'][i]])))
                            power['certo_UHF'] = power['certo_UHF'][:m]
                            power[chain_prn] = np.array(df_chain['power_d'][:m])
                            
                            m = min(len(phase['certo']), len(np.array(df_chain['phase_d'][df_cut['start'][i]:df_cut['end'][i]])))
                            phase['certo'] = phase['certo'][:m]
                            phase[chain_prn] = np.array(df_chain['phase_d'][:m])
                            
                            # Setting up plots for power data
                            fig = plt.figure()
                            ax1 = plt.subplot2grid((3,1), (0,0))
                            ax2 = plt.subplot2grid((3,1), (1,0))
                            ax3 = plt.subplot2grid((3,1), (2,0))
                            fig.tight_layout()
                            
                            # Setting the length of the axis for all plots
                            ax1.set(title='VHF Power at CERTO')
                            ax2.set(ylabel='Value', title='UHF Power at CERTO')
                            ax3.set(xlabel='Index', title='Power at CHAIN ' + chain_prn)
                            
                            # Plotting power data
                            ax1.plot(power['certo_VHF'])
                            ax2.plot(power['certo_UHF'])
                            ax3.plot(power[chain_prn])
                            
                            # Setting up plots for phase data
                            fig = plt.figure()
                            ax4 = plt.subplot2grid((2,1), (0,0))
                            ax5 = plt.subplot2grid((2,1), (1,0))
                            fig.tight_layout()
                            
                            # Setting the length of the axis for all plots
                            ax4.set(ylabel='Value',title='VHF Phase at CERTO')
                            ax5.set(xlabel='Index', title='Phase at CHAIN ' + chain_prn)
                            
                            # Plotting phase data
                            ax4.plot(phase['certo'])
                            ax5.plot(phase[chain_prn])
                            plt.show()
                            
                except ValueError:
                    # Do nothing
                    pass
                
