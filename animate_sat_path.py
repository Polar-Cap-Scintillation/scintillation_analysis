#animate_sat_path.py
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import animation
import os

def update_points(i, x_cor, y_cor, z_cor, points_xy, points_xz, points_yz):
    
    # Find the new sets of coordinates here. The resulting arrays should 
    # have the same shape as the original x,y,z
    new_x = [a[0:i*500] for a in x_cor.values()]
    new_y = [a[0:i*500] for a in y_cor.values()]
    new_z = [a[0:i*500] for a in z_cor.values()]
    
    # update properties
    for j in range(len(points_xy)):
        points_xy[j].set_data(new_x[j],new_y[j])
        points_xz[j].set_data(new_x[j],new_z[j])
        points_yz[j].set_data(new_y[j],new_z[j])
        
    # Since we need to return a sequence of Artist objects and not a list of them
    # we can compound all of the artist into a tuple and return that
    points = tuple(points_xy) + tuple(points_xz) + tuple(points_yz)
    # return modified artists
    return points

# def polar_animator(i, trail=40):
#     l1.set_data(x[0:i*100], y[0:i*100])
#     l2.set_data(x[0:i*100], z[0:i*100])
#     l3.set_data(y[0:i*100], z[0:i*100])
#     return l1,l2,l3,

# certo_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2017"
certo_path = r"/media/sf_vm_share/Resolute/Data/2017"

# chain_path = r"E:\vm_share\chain_data\RESreadable"
chain_path = r"/media/sf_vm_share/chain_data/RESreadable"

# save_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\images"
save_path = r"/media/sf_VirtualboxShare/images"

file = "filenames2.gif"
complete_name = os.path.join(save_path, file)

Rearth = 6378 # km

# Find how many .its files exist in directory
# its_files = 0
# for paths in certo_path:
#     os.chdir(paths)
#     for file in os.listdir():
#         if file.endswith('.its'):
#             its_files += 1

# Iterate through all files
current_file = 0
# for paths in certo_path:
os.chdir(certo_path)
for file in os.listdir():
    data_file_path = f"{certo_path}/{file}"
    
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
                x_cor[chain_prn] = np.array(df['x_corr'])
                y_cor[chain_prn] = np.array(df['y_corr'])
                z_cor[chain_prn] = np.array(df['z_corr'])
                
        # Return the max of the absolute value of the largest or smallest value 
        # in the position array or the radius of Earth for determining the axis
        xaxis = np.max([max(abs(np.min(a)),abs(np.max(a))) for a in x_cor.values()])+1000
        yaxis = np.max([max(abs(np.min(a)),abs(np.max(a))) for a in y_cor.values()])+1000
        zaxis = np.max([max(abs(np.min(a)),abs(np.max(a))) for a in z_cor.values()])+1000
        
        # Took this from: https://nickcharlton.net/posts/drawing-animating-shapes-matplotlib.html
        # These are the exact same thing as different variables because you cannot
        # re-use an artist in more than one axes as this is not supported
        # It's really that dumb and at the time of writting I'm upset
        earth1 = plt.Circle((0, 0), radius=Rearth, fc='b')
        earth2 = plt.Circle((0, 0), radius=Rearth, fc='b')
        earth3 = plt.Circle((0, 0), radius=Rearth, fc='b')
        
        fig = plt.figure()
        ax1 = plt.subplot2grid((2,2), (0,0), rowspan=2)
        ax2 = plt.subplot2grid((2,2), (0,1))
        ax3 = plt.subplot2grid((2,2), (1,1))
        fig.tight_layout()
        
        # Setting the length of the axis for all plots
        ax1.set(xlim=(-xaxis, xaxis), ylim=(-yaxis, yaxis), xlabel='x axis [km]', ylabel='y axis [km]', title='satellite\'s orbit')
        ax2.set(xlim=(-xaxis, xaxis), ylim=(-zaxis, zaxis), xlabel='x axis [km]', ylabel='z axis [km]')
        ax3.set(xlim=(-yaxis, yaxis), ylim=(-zaxis, zaxis), xlabel='y axis [km]', ylabel='z axis [km]')
        
        # Add Earth to plots
        ax1.add_patch(earth1)
        ax2.add_patch(earth2)
        ax3.add_patch(earth3)
        
        # Preallocating the length of the list for the plots
        points_xy_l = list(range(len(x_cor)))
        points_xz_l = list(range(len(y_cor)))
        points_yz_l = list(range(len(z_cor)))
        
        # Sets up the plotting of all satellites on each plot
        for ia, a in enumerate(x_cor.values()):
            for ib, b in enumerate(y_cor.values()):
                for ic, c in enumerate(z_cor.values()):
                    if(ia == ib):
                        points_xy_l[ia] = ax1.plot(a[0],b[0],'-', color='C' + str(ia))
                    if(ia == ic):
                        points_xz_l[ia] = ax2.plot(a[0],c[0],'-', color='C' + str(ia))
                    if(ib == ic):
                        points_yz_l[ib] = ax3.plot(b[0],c[0],'-', color='C' + str(ib))
        
        # For some reason the above creates a list of list which we don't want
        # Use this to convert from list of list to a list
        points_xy = []
        points_xz = []
        points_yz = []
        for sublist in points_xy_l:
            for item in sublist:
                points_xy.append(item)
        for sublist in points_xz_l:
            for item in sublist:
                points_xz.append(item)
        for sublist in points_yz_l:
            for item in sublist:
                points_yz.append(item)
                
        # points_xy = ax1.plot([a[0] for a in x_cor.values()],[a[0] for a in y_cor.values()], 'o-', color='g')
        # points_xz = ax2.plot([a[0] for a in x_cor.values()],[a[0] for a in z_cor.values()], 'o-', color='g')
        # points_yz = ax3.plot([a[0] for a in y_cor.values()],[a[0] for a in z_cor.values()], 'o-', color='g')
        
        # l1, = ax1.plot([], [], 'o-', markevery=[-1],color='b') # xy
        # l2, = ax2.plot([], [], 'o-', markevery=[-1],color='b') # xz
        # l3, = ax3.plot([], [], 'o-', markevery=[-1],color='b') # yz
        
        ani = animation.FuncAnimation(fig, update_points, frames=int(len(x)/500), fargs=(x_cor,y_cor,z_cor,points_xy,points_xz,points_yz), interval=5, blit=True)
        writergif = animation.PillowWriter(fps=60)
        ani.save(complete_name,writer=writergif)
        
        break
        
    except ValueError:
        # Do nothing
        pass

    # print('Completed file ' + str(current_file) + ' of ' + str(its_files))
    
    # Change back to certo path for loop
    os.chdir(certo_path)