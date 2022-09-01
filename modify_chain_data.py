#addon_ele_to_chain_data.py
import datetime as dt
from skyfield.api import EarthSatellite,load, wgs84, Topos
import pytz
import os
import pandas as pd
import math as ma
from pymap3d import aer2ecef
# from spacetrack import SpaceTrackClient
# import spacetrack.operators as op
# from space_track_credentials import ST_USERNAME, ST_PASSWORD


def create_new_file_with_elevation_angle(df_data,df,file_name,lat,lon,file_name_prn):
    
    # Generate time array. Original data is in UTC seconds. We need timezone aware datetime
    utime = [dt.datetime.utcfromtimestamp((df_data['UTC'][i])) for i in range(len(df_data['UTC']))]
    utime_aware = [utime[i].replace(tzinfo=pytz.UTC) for i in range(len(utime))]
    
    # Parse the datetime out of the file name
    file_date = dt.datetime.strptime(file_name, '%Y%m%d%H%M%S')
    
    # Find TLE from closest epoch
    TLE_index = binary_search_index(df['TLE_EPOCH'], 0, len(df['TLE_EPOCH'])-1, file_date)
    
    # I don't really understand what timescale is but everything in skyfield uses it
    ts = load.timescale()
    
    # Create the Satellite object
    satellite = EarthSatellite(df['TLE_LIST'][TLE_index][0], df['TLE_LIST'][TLE_index][1], 'whatname',ts)
    rbo = Topos(lat, lon)
    time = ts.from_datetimes(utime_aware)
    el, az, rng = (satellite - rbo).at(time).altaz()
    
    xyz = aer2ecef(az.degrees, el.degrees, rng.m, lat, lon, 145, ell=None, deg=True)
    
    df_new = pd.read_pickle(file_name_prn)
    
    # Convert data to a dataframe to write to file
    df_new['x_coor'] = xyz[0]
    df_new['y_coor'] = xyz[1]
    df_new['z_coor'] = xyz[2]
    
    # Remove unessisary/incorrect information from current dataframe
    del df_new["x_corr"]
    del df_new["y_corr"]
    del df_new["z_corr"]
    del df_new["x_vel"]
    del df_new["y_vel"]
    del df_new["z_vel"]
    
    return df_new

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
    TLE_epoch = ['']*len(df_gps)
    TLE_list = [['','']]*len(df_gps)

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
        TLE_list[index] = [[split[2*i],split[2*i+1]] for i in range(len(split)//2)]
        
        # extract epoch from each TLE
        TLE_epoch[index] = [dt.datetime.strptime(tle[0][18:23],'%y%j')+dt.timedelta(days=float(tle[0][23:32])) for tle in TLE_list[index]]
        
    df_tle = pd.DataFrame(
        {
            "TLE_EPOCH":TLE_epoch,
            "TLE_LIST":TLE_list
        }
    )
    
    # Concatenate TLE_EPOCH and TLE_LIST to the dataframe
    df_new = pd.concat([df_gps,df_tle],axis=1)
        
    return df_new


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
    
    resolute_bay_lat_chain = 74.746627
    resolute_bay_long_chain = 264.997469
    
    # Folder containing CHAIN satellite data pickle files
    # time_path = r"/media/sf_vm_share/chain_data/chain_pickle_extract"
    time_path = r"E:\vm_share\chain_data\chain_pickle_extract"
    
    # Folder containing old CHAIN data pickle files
    # old_data_path = r"/media/sf_vm_share/chain_data/RESreadable_no_azi"
    old_data_path = r"E:\vm_share\chain_data\RESreadable_pre_fix"
    
    # Save Path
    # save_path = r"/media/sf_vm_share/chain_data/RESreadable"
    save_path = r"E:\vm_share\chain_data\RESreadable"
    
    # Change the directory
    os.chdir(time_path)
    
    # Dataframe of the list of GPS satellites
    # df_gps = pd.read_csv(r"/media/sf_git/scintillation_analysis/GPS_Satellites_Effective_Times.csv")
    
    # Getting all the TLE and epoch values from the all of the GPS satellites
    # df_gps = find_all_gps_satellite_tle(df_gps)
    # df_gps.to_pickle(r"/media/sf_vm_share/chain_data/gps_data.pkl")
    # df_gps = pd.read_pickle(r"/media/sf_vm_share/chain_data/gps_data.pkl")
    df_gps = pd.read_pickle(r"E:\vm_share\chain_data\gps_data.pkl")
    print('Collected the satellite data')
    
    # Find how many files exist in directory
    files = len([file for file in os.listdir()])
    # Iterate through all files
    current_file = 0
    for file in os.listdir():
        current_file += 1
        current_sat = 0
        file_path = f"{time_path}/{file}"
        df_data = pd.read_pickle(file_path)
        # Iterate through all satellites
        for i in range(len(df_data)):
            current_sat += 1
            srn = find_gps_satellite_row_number(df_data.loc[i]['sat_list'][1:],os.path.splitext(file[3:-8])[0],df_gps)
            file_path_prn = os.path.join(old_data_path, os.path.splitext(file[0:-8])[0] + 'prn' + df_data.loc[i]['sat_list'][1:] + '.pkl') # prn file path
            df = create_new_file_with_elevation_angle(df_data.loc[i],df_gps.loc[srn],os.path.splitext(file[3:-8])[0],resolute_bay_lat_chain,resolute_bay_long_chain,file_path_prn)
            # Write new data to a file
            completename = os.path.join(save_path, os.path.splitext(file[0:-8])[0] + 'prn' + df_data.loc[i]['sat_list'][1:] + '.pkl')
            df.to_pickle(completename)
                
            print('Completed satellite ' + str(current_sat) + ' of ' + str(len(df_data)))
        print('Completed file ' + str(current_file) + ' of ' + str(files))
    
    
    
if __name__=='__main__':
    main()