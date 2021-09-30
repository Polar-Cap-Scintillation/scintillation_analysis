#create_readable_chain_data.py
#Creates readable chain data files similar to what is created in parse_certo.py
import numpy as np
import datetime as dt
from sgp4.api import Satrec # pip install sgp4
import pandas as pd
import math as ma
import h5py
import itertools
import os
from spacetrack import SpaceTrackClient
import spacetrack.operators as op
from detrend import power_detrend, phase_detrend
from scint_index import S_4, sigma_phi
from space_track_credentials import ST_USERNAME, ST_PASSWORD



def parse_chain_hdf5(df_data,df,file_name,window):

    # Read satellite data
    power = np.array(df_data['power'])
    phase = np.array(df_data['phase'])
    
    # Generate time array
    utime = np.array(df_data['UTC'])
    
    # Parse the datetime out of the file name
    file_date = dt.datetime.strptime(file_name, '%Y%m%d%H%M%S')
    
    # Find TLE from closest epoch
    TLE_index = binary_search_index(df['TLE_EPOCH'], 0, len(df['TLE_EPOCH'])-1, file_date)
    
    # Get information on satellite positional data from sgp4
    satellite = Satrec.twoline2rv(df['TLE_LIST'][TLE_index][0], df['TLE_LIST'][TLE_index][1])
    
    # Convert utime from utc seconds to Timestamp to convert to julian date
    # Conversion may be a few leap seconds off
    jd = utime / 86400.0 + 2440587.5
    
    # sgp4 needs two separate variables for julian time
    fr = jd % 1
    jd = np.array([int(jds) for jds in jd])
    
    # Calculate true equator mean equinox position and velocity
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
    power_detrended = power_detrend(utime,power)
    phase_detrended = phase_detrend(utime,phase)
    
    # Calculate S_4 and sigma_phi for VHF and UHF
    try:
    # For scintillation data that have too few points the windowing becomes larger
    # than the amount of data and so it shouldn't be considered both because we
    # cannot calculate it and because it would be too short of an event to record
        GPS_S_4 = S_4(utime, power_detrended, window)
        GPS_sigma_phi = sigma_phi(utime, phase_detrended, window)
    except ValueError:
        return pd.DataFrame(), False
    
    # Convert data to a datafrom to write to file
    df = pd.DataFrame({'power' : power, 'phase' : phase, 'power_d' : power_detrended,
                       'phase_d' : phase_detrended, 'S_4' : GPS_S_4, 'sigma_phi' : GPS_sigma_phi, 
                       'x_corr' : xcorr, 'y_corr' : ycorr, 'z_corr' : zcorr, 'x_vel' : xvel, 
                       'y_vel' : yvel, 'z_vel' : zvel})
    
    return df, True


def find_gps_satellite_row_number(prn,file_name,df_gps):
    
    # Filter relevent prn numbered satellites
    prn = int(prn)
    
    # Parse the datetime out of the file name
    file_date = dt.datetime.strptime(file_name, '%Y%m%d%H%M%S')
    
    # Get start time and end time for each prn to find what timeframe the satellite falls into
    for index, row in df_gps.iterrows():
        # Is there a better way to get the start time and end time out from 
        # separate indices of Y m d H M S?
        
        # Only checking the prn that matches the satellite
        if row['PRN'] == prn:
            
            start_time = []
            end_time = []
            for i in range(3,9):
                start_time.append(int(row[i]))
            start_date = dt.datetime(*start_time)
            
            # For the case of nan from an incomplete satellite duration lacking an end time
            if not ma.isnan(row[9]):
                for i in range(9,15):
                    end_time.append(int(row[i]))
                end_date = dt.datetime(*end_time)
            else: 
                end_date = dt.datetime.now()
            
            # Returns index within the GPS_Satellites_Effective_Times.csv file
            if file_date > start_date and file_date < end_date:
                return index
    
    # If it gets this far then something went wrong and the 
    # satellite either doesn't exist or is too new and 
    # GPS_Satellites_Effective_Times.csv needs to be updated
    raise ValueError("Input satellite does not match any in database")


def find_all_gps_satellite_tle(df_gps):
    # the program should stall here due to how many request it sends to Space-Track.org
    
    # get two line element from Space-Track.org
    st = SpaceTrackClient(identity=ST_USERNAME, password=ST_PASSWORD)
    
    # add spots in the dataframe for TLE_EPOCH and TLE_LIST
    df_gps['TLE_EPOCH'] = ''
    df_gps['TLE_LIST'] = ''
    
    for index, row in df_gps.iterrows():
        # Get start time and end time
        start_time = []
        end_time = []
        for i in range(3,9):
            start_time.append(int(row[i]))
        start_date = dt.datetime(*start_time)
        
        # For the case of nan from an incomplete satellite duration lacking an end time
        if not ma.isnan(row[9]):
            for i in range(9,15):
                end_time.append(int(row[i]))
            end_date = dt.datetime(*end_time)
        else: 
            end_date = dt.datetime.now()
        
        # get list of tles for a satellite
        output = st.tle(norad_cat_id=row['NORAD_ID'], orderby='epoch asc', epoch=op.inclusive_range(start_date,end_date), format='tle')
        
        # parse output into list of distinct TLEs
        split = output.splitlines()
        TLE_list = [[split[2*i],split[2*i+1]] for i in range(len(split)//2)]
        
        # extract epoch from each TLE
        TLE_epoch = [dt.datetime.strptime(tle[0][18:23],'%y%j')+dt.timedelta(days=float(tle[0][23:32])) for tle in TLE_list]
        
        # Assign TLE_EPOCH and TLE_LIST to the dataframe
        df_gps['TLE_EPOCH'][index] = TLE_epoch
        df_gps['TLE_LIST'][index] = TLE_list
        
    return df_gps


# Got this from https://www.geeksforgeeks.org/python-program-for-binary-search/
# This is a recursive binary search to find a close enough epoch to match with a TLE
def binary_search_index(arr, low, high, x):

    # Check base case
    if high >= low:

        mid = (high + low) // 2

        # If element is present at the middle itself
        if arr[mid] == x:
            return mid

        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif arr[mid] > x:
            return binary_search_index(arr, low, mid - 1, x)

        # Else the element can only be present in right subarray
        else:
            return binary_search_index(arr, mid + 1, high, x)

    else:
        # Element is close enough to this timestamp
        return high
        
    
def main():
    
    # Set window to value between 10-60
    window = 10
    
    # Folder containing CHAIN pickle files
    path = r"/media/sf_vm_share/chain_data/chain_pickle_extract"
    #path = r"C:\Users\TateColby\Desktop\VirtualboxShare\RES\Decompressed"
    # Save Path
    save_path = r"/media/sf_vm_share/chain_data/RESreadable"
    #save_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\RESreadable"
    
    # Change the directory
    os.chdir(path)
    
    # Dataframe of the list of GPS satellites
    df_gps = pd.read_csv(r"/media/sf_git/scintillation_analysis/GPS_Satellites_Effective_Times.csv")
    #df_gps = pd.read_csv(r'C:\Users\TateColby\git\scintillation_analysis\GPS_Satellites_Effective_Times.csv')
    
    # Getting all the TLE and epoch values from the all of the GPS satellites
    df_gps = find_all_gps_satellite_tle(df_gps)
    
    # Find how many files exist in directory
    files = len([file for file in os.listdir()])
    
    # Iterate through all files
    current_file = 0
    for file in os.listdir():
        current_file += 1
        current_sat = 0
        file_path = f"{path}/{file}"
        df_data = pd.read_pickle(file_path)
        # Iterate through all satellites
        for i in range(len(df_data)):
            current_sat += 1
            srn = find_gps_satellite_row_number(df_data.loc[i]['sat_list'][1:],os.path.splitext(file[3:-8])[0],df_gps)
            df, validity = parse_chain_hdf5(df_data.loc[i],df_gps.loc[srn],os.path.splitext(file[3:-8])[0],window)
            # Write new data to a file
            if validity:
                completename = os.path.join(save_path, os.path.splitext(file[0:-8])[0] + 'prn' + df_data.loc[i]['sat_list'][1:] + '.pkl')
                df.to_pickle(completename)
                
            print('Completed satellite ' + str(current_sat) + ' of ' + str(len(df_data)))
        print('Completed file ' + str(current_file) + ' of ' + str(files))
        
        
if __name__=='__main__':
    main()
    