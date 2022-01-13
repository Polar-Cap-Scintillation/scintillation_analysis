#plot_sat_above_res.py
import numpy as np
import os
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap, BoundaryNorm
from pymap3d import ecef2aer, aer2geodetic
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import datetime as dt

cutoff_file = r"E:\vm_share\conjunctions\cutoff15conjunctions.csv"
# cutoff_file = r"/media/sf_vm_share/conjunctions/cutoff15conjunctions.csv"

certo_path = [r"E:\vm_share\Resolute\Data\2017",
            r"E:\vm_share\Resolute\Data\2018"]
# certo_path = [r"/media/sf_VirtualboxShare/Resolute/Data/2017",
#             r"/media/sf_VirtualboxShare/Resolute/Data/2018"]

chain_path = r"E:\vm_share\chain_data\RESreadable"
#chain_path = r"/media/sf_vm_share/chain_data/RESreadable"

# Resolute Bay position
resolute_bay_lat_certo = 74.72955
resolute_bay_long_certo = 360-94.90576
resolute_bay_lat_chain = 74.746627
resolute_bay_long_chain = 264.997469

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
                    
                    _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, _, \
                        x, y, z, _, _, _, = np.genfromtxt(data_file_path,skip_header=8,unpack=True, delimiter = ",")
                    
                    x_cor = {'certo':x[df_cut['start'][i]:df_cut['end'][i]]}
                    y_cor = {'certo':y[df_cut['start'][i]:df_cut['end'][i]]}
                    z_cor = {'certo':z[df_cut['start'][i]:df_cut['end'][i]]}
                    
                    # Find matching CHAIN data to CERTO data
                    os.chdir(chain_path)
                    for chain_file in os.listdir():
                        if chain_file[3:-9] == file[3:-5] and df_cut['sat'][i] == chain_file[17:22]:
                            chain_file_path = f"{chain_path}/{chain_file}"
                            df = pd.read_pickle(chain_file_path)
                            chain_prn = chain_file[17:22]
                            
                            # Using this to match the length of the CERTO and CHAIN datasets
                            # https://stackoverflow.com/questions/63937664/match-length-of-arrays-in-python
                            m = min(len(x_cor['certo']), len(np.array(df['x_corr'][df_cut['start'][i]:df_cut['end'][i]])))
                            x_cor['certo'] = x_cor['certo'][:m]
                            x_cor[chain_prn] = np.array(df['x_corr'][:m])
                            
                            m = min(len(y_cor['certo']), len(np.array(df['y_corr'][df_cut['start'][i]:df_cut['end'][i]])))
                            y_cor['certo'] = y_cor['certo'][:m]
                            y_cor[chain_prn] = np.array(df['y_corr'][:m])
                            
                            m = min(len(z_cor['certo']), len(np.array(df['z_corr'][df_cut['start'][i]:df_cut['end'][i]])))
                            z_cor['certo'] = z_cor['certo'][:m]
                            z_cor[chain_prn] = np.array(df['z_corr'][:m])
                    
                    # Calculate the azimuth, elevatoin, and slant range from Resolute Bay
                    azi_ele = {}
                    lat_long = {}
                    hav = {}
                    theta = {}
                    azi_ele['certo'] = ecef2aer(x_cor['certo']*100, y_cor['certo']*100, z_cor['certo']*100, resolute_bay_lat_certo, resolute_bay_long_certo, 145, deg=True)
                    lat_long['certo'] = aer2geodetic(azi_ele['certo'][0], azi_ele['certo'][1], azi_ele['certo'][2], resolute_bay_lat_certo, resolute_bay_long_certo, 0, ell=None, deg=True)
                    for sat in x_cor:
                        if sat != 'certo':
                            # Calculate he azimuth with input degrees and output radians
                            azi_ele[sat] = ecef2aer(x_cor[sat]*100, y_cor[sat]*100, z_cor[sat]*100, resolute_bay_lat_chain, resolute_bay_long_chain, 0, deg=True)
                            # It's dumb that there isn't a single function that calculates the lat and long from xyz coor
                            lat_long[sat] = aer2geodetic(azi_ele[sat][0], azi_ele[sat][1], azi_ele[sat][2], resolute_bay_lat_chain, resolute_bay_long_chain, 0, ell=None, deg=True)
                    
                    fig = plt.figure(figsize=(15,15))
                    ax = plt.subplot(projection=ccrs.PlateCarree())
                    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'ocean', '50m', facecolor='lightblue'))
                    ax.add_feature(cfeature.NaturalEarthFeature('physical', 'land', '50m', facecolor='lightgrey'))
                    ax.coastlines(resolution='50m', color='grey', linewidth=0.5)
                    ax.gridlines()
                    # Compute a circle in axes coordinates, which we can use as a boundary
                    # for the map. We can pan/zoom as much as we like - the boundary will be
                    # permanently circular.
                    # theta = np.linspace(0, 2*np.pi, 100)
                    # center, radius = [0.5, 0.5], 0.5
                    # verts = np.vstack([np.sin(theta), np.cos(theta)]).T
                    # circle = mpath.Path(verts * radius + center)

                    # ax.set_boundary(circle, transform=ax.transAxes)
                    ax.set_extent([-60, -10, 50, 75], crs=ccrs.PlateCarree())
                    ax.set_title('CERTO and CHAIN paths starting at: ' + str(dt.datetime.strptime(str(file[3:-5]),'%Y%m%d%H%M%S')), fontsize=30)
                    
                    # mpl.rcParams['axes.prop_cycle'] = cycler.cycler('color', color)
                    # plot CERTO and CHAIN
                    colormap = np.arange(len(lat_long['certo'][0]))
                    for sat in x_cor:
                        # This is for creating the spectrum line for a time series
                        # Modified from: https://matplotlib.org/stable/gallery/lines_bars_and_markers/multicolored_line.html
                        
                        # Create a set of line segments so that we can color them individually
                        # This creates the points as a N x 1 x 2 array so that we can stack points
                        # together easily to get the segments. The segments array for line collection
                        # needs to be (numlines) x (points per line) x 2 (for x and y)
                        points = np.array([lat_long[sat][1], lat_long[sat][0]]).T.reshape(-1, 1, 2)
                        segments = np.concatenate([points[:-1], points[1:]], axis=1)

                        # Create a continuous norm to map from data points to colors
                        norm = plt.Normalize(colormap.min(), colormap.max())
                        lc = LineCollection(segments, cmap='jet', norm=norm, linewidths=100)
                        # Set the values used for colormapping
                        lc.set_array(colormap)
                        lc.set_linewidth(1)
                        line = ax.add_collection(lc)
                        # fig.colorbar(line, ax=ax)
                        ax.plot(lat_long[sat][1][0], lat_long[sat][0][0], marker='o', linewidth=1, label=sat, transform=ccrs.PlateCarree())
                        
                    ax.legend(loc='lower right',fontsize=30)
                    
                    plt.show()
                    
                except ValueError:
                    # Do nothing
                    pass
                
            