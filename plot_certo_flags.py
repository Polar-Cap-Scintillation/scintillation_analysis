#plot_certo_flags.py
# Import Module
import numpy as np
import os
from matplotlib import pyplot as plt

# Used for finding the row index of the unessisary data at the end of .pro files
# Taken from: https://stackoverflow.com/questions/15718068/search-file-and-find-exact-match-and-print-line
def lines_that_contain(string, fp):
    return [index for index, line in enumerate(fp) if string in line]


# datapath = r"/media/sf_VirtualboxShare/Resolute/Data/2018"
# propath = r"/media/sf_VirtualboxShare/Resolute/2018"
datapath = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2018"
propath = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\2018"

# Change the directory
os.chdir(datapath)

# Iterate through all files
for file in os.listdir():
    data_file_path = f"{datapath}/{file}"
    profile = file[3:-4] + '.pro'
    pro_file_path = f"{propath}/{profile}"
    
    # Some files lack data and need to be thrown out
    try:
        # Getting data from the data files
        # Order is index,VHF_pow,VHF_pha,UHF_pow,UHF_pha,VHF_pow_d,VHF_pha_d,UHF_pow_d,UHF_pha_d,
        # VHF_S_4,UHF_S_4,VHF_sigma_phi,UHF_sigma_phi,x_corr,y_corr,z_corr,x_vel,y_vel,z_vel
        _, VHF_pow, VHF_pha, UHF_pow, _, VHF_pow_d, VHF_pha_d, UHF_pow_d, _, VHF_S_4, UHF_S_4, VHF_sigma_phi, _, \
            _, _, _, _, _, _, = np.genfromtxt(data_file_path,skip_header=8,unpack=True, delimiter = ",")
        
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
        
        UHF_pow_f = np.repeat(UHF_pow_f,data_rate)
        VHF_pow_f = np.repeat(VHF_pow_f,data_rate)
        phasef = np.repeat(phasef,data_rate)
        
        time = np.arange(len(UHF_pow_f))
        
        UHF_pow_interp = np.copy(UHF_pow[0:len(UHF_pow_f)])
        VHF_pow_interp = np.copy(VHF_pow[0:len(UHF_pow_f)])
        VHF_pha_interp = np.copy(VHF_pha[0:len(UHF_pow_f)])
        
        UHF_pow_interp[UHF_pow_f!=0] = np.interp(time[UHF_pow_f!=0], time[UHF_pow_f==0], UHF_pow_interp[UHF_pow_f==0],right=np.nan)
        VHF_pow_interp[VHF_pow_f!=0] = np.interp(time[VHF_pow_f!=0], time[VHF_pow_f==0], VHF_pow_interp[VHF_pow_f==0],right=np.nan)
        VHF_pha_interp[phasef!=0] = np.interp(time[phasef!=0], time[phasef==0], VHF_pha_interp[phasef==0],right=np.nan)
        
        # Is matplotlib for real here?
        color1 = 'tab:blue'
        color2 = 'tab:red'
        color3 = 'tab:green'
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('Time index')
        ax1.set_ylabel('UHF power Value', color=color1)
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.plot(UHF_pow[0:len(UHF_pow_f)], color=color1)
        ax2.plot(UHF_pow_interp, color=color2)
        ax2.tick_params(axis='y', labelcolor=color1)
        ax1.set_ylabel('Flag Value', color=color3)  # we already handled the x-label with ax1
        ax1.plot(UHF_pow_f, color=color3)
        ax1.tick_params(axis='y', labelcolor=color3)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.title('UHF power and flag')
        plt.show()
        
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('Time index')
        ax1.set_ylabel('VHF power Value', color=color1)
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.plot(VHF_pow[0:len(UHF_pow_f)], color=color1)
        ax2.plot(VHF_pow_interp, color=color2)
        ax2.tick_params(axis='y', labelcolor=color1)
        ax1.set_ylabel('Flag Value', color=color3)  # we already handled the x-label with ax1
        ax1.plot(VHF_pow_f, color=color3)
        ax1.tick_params(axis='y', labelcolor=color3)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.title('VHF power and flag')
        plt.show()
        
        fig, ax1 = plt.subplots()
        ax1.set_xlabel('Time index')
        ax1.set_ylabel('VHF phase Value', color=color1)
        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        ax2.plot(VHF_pha[0:len(UHF_pow_f)], color=color1)
        ax2.plot(VHF_pha_interp, color=color2)
        ax2.tick_params(axis='y', labelcolor=color1)
        ax1.set_ylabel('Flag Value', color=color3)  # we already handled the x-label with ax1
        ax1.plot(phasef, color=color3)
        ax1.tick_params(axis='y', labelcolor=color3)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.title('VHF phase and flag')
        plt.show()
        
        # plt.figure(1)
        # plt.plot(UHF_pow)
        # plt.plot(UHF_pow_f)
        # plt.xlabel("Value")
        # plt.ylabel("Count")
        # plt.title('UHF S_4 and flag')
        
        # plt.figure(2)
        # plt.plot(VHF_pow)
        # plt.plot(VHF_pow_f)
        # plt.xlabel("Value")
        # plt.ylabel("Count")
        # plt.title('VHF S_4 and flag')
        
        # plt.figure(3)
        # plt.plot(VHF_pha)
        # plt.plot(phasef)
        # plt.xlabel("Value")
        # plt.ylabel("Count")
        # plt.title('VHF sigma_phi and flag')
        # plt.show()
    except ValueError:
        # Do nothing
        pass
    