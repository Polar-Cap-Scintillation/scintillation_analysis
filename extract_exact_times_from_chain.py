#extract_exact_times_from_chain.py
import numpy as np
import datetime as dt
import h5py
import os
from chain_raw_data_from_certo_times import hour_floor, hour_ceiling
import pandas as pd

# Modified from https://www.geeksforgeeks.org/python-program-for-binary-search/
# This is a recursive binary search to find if CHAIN start and end times are close enough to CERTO
def binary_search_index_delta(arr, low, high, x, delta):

    # Check base case
    if high >= low:

        mid = (high + low) // 2

        # If element is present at the middle itself
        if arr[mid] == x:
            return mid

        # If element is smaller than mid, then it can only
        # be present in left subarray
        elif arr[mid] > x:
            return binary_search_index_delta(arr, low, mid - 1, x, delta)

        # Else the element can only be present in right subarray
        else:
            return binary_search_index_delta(arr, mid + 1, high, x, delta)

    else:
        if x - delta < arr[high] < x + delta:
            # Element is close enough to this timestamp
            return high
        else:
            return -1


def identify_useable_satllites(time_range,front,rear,chain_path,sub_folder,timestamp,time_delta):
    # Check 1
    sat_list = []
    temp = []
    total = set()
    first_run = True
    for time in time_range:
        
        # Finding the relevant file names
        middle = time.strftime('%Y%m%d%H%M%S')
        file_name = front + middle + rear
        file_path = f"{chain_path}\{file_name}"
        
        # Iterate through all satellites
        f = h5py.File(file_path,'r')
        for sat in f:
            temp.append(sat)
        # Need a list to first compare the list to
        if first_run:
            for sat in f:
                sat_list.append(sat)
        total = set(sat_list).intersection(temp)
        temp = []
        sat_list = list(total)
        first_run = False
    
    sat_list.sort()
    
    # Check to see if sat_list is an empty list
    if not sat_list:
        return pd.DataFrame(), False
    
    # Check 2
    start_time_index = [-1] * len(sat_list)
    end_time_index = [-1] * len(sat_list)
    # Check to see if time range covers multiple hours 
    for time in time_range:
        # Finding the relevant file names for the satellites
        middle = time.strftime('%Y%m%d%H%M%S')
        file_name = front + middle + rear
        file_path = f"{chain_path}\{file_name}"
        f = h5py.File(file_path,'r')
        
        # Check to see if satellites cover start and end time check wihin second or so
        for sat_index, sat in enumerate(sat_list):
            sat_path = f[sat + '/' + sub_folder]
            utime = sat_path['UTC'][()]
            if start_time_index[sat_index] == -1:
                start_time_index[sat_index] = find_nearest_time(utime,timestamp[0],time_delta)
            if end_time_index[sat_index] == -1:
                end_time_index[sat_index] = find_nearest_time(utime,timestamp[1],time_delta)
    
    sat_list_2 = []
    start_time_index_2 = []
    end_time_index_2 = []
    for sat_index, sat in enumerate(sat_list):
        if start_time_index[sat_index] != -1 and end_time_index[sat_index] != -1:
            sat_list_2.append(sat)
            start_time_index_2.append(start_time_index[sat_index])
            end_time_index_2.append(end_time_index[sat_index])
    
    # Check to see if sat_list is an empty list
    if not sat_list_2:
        return pd.DataFrame(), False
    
    # Check 3
    # Create a continuous time array to check though
    continuity_index = [True] * len(sat_list_2)
    utime = np.empty((len(sat_list_2),0)).tolist()
    # Check length of time range
    if len(time_range) == 1:
        # The time range covers one hour so it is easier to parse all the data
        # Finding the relevant file names for the satellites
        middle = time_range[0].strftime('%Y%m%d%H%M%S')
        file_name = front + middle + rear
        file_path = f"{chain_path}\{file_name}"
        f = h5py.File(file_path,'r')
        for sat_index, sat in enumerate(sat_list_2):
            sat_path = f[sat + '/' + sub_folder]
            utime[sat_index].extend(sat_path['UTC'][start_time_index_2[sat_index]:end_time_index_2[sat_index]])
    else:
        
        for time_index, time in enumerate(time_range):
            # Finding the relevant file names for the satellites
            middle = time.strftime('%Y%m%d%H%M%S')
            file_name = front + middle + rear
            file_path = f"{chain_path}\{file_name}"
            f = h5py.File(file_path,'r')
            # During the first pass we only collect data from after the start time index of the event
            if time_index == 0:
                for sat_index, sat in enumerate(sat_list_2):
                    sat_path = f[sat + '/' + sub_folder]
                    utime[sat_index].extend(sat_path['UTC'][start_time_index_2[sat_index]:])
            # For any potential intermediate steps we collect data from the whole file
            # This likely should never occur as events should only a last maximum duration of 20 minutes
            elif time_index != (len(time_range)-1):
                for sat_index, sat in enumerate(sat_list_2):
                    sat_path = f[sat + '/' + sub_folder]
                    utime[sat_index].extend(sat_path['UTC'][()])
            # When we know we are taking data from the last file we want to stop at the end point of the event
            else:
                for sat_index, sat in enumerate(sat_list_2):
                    sat_path = f[sat + '/' + sub_folder]
                    utime[sat_index].extend(sat_path['UTC'][:end_time_index_2[sat_index]])
            
    # Check for time continuity
    for sat_index in range(len(sat_list_2)):
        
        for i in range(len(utime)-1):
            if abs(utime[sat_index][i]-utime[sat_index][i+1]) > time_delta:
                continuity_index[sat_index] == False
        
    sat_list_3 = []
    start_time_index_3 = []
    end_time_index_3 = []
    for sat_index, sat in enumerate(sat_list_2):
        if continuity_index[sat_index]:
            sat_list_3.append(sat)
            start_time_index_3.append(start_time_index_2[sat_index])
            end_time_index_3.append(end_time_index_2[sat_index])
    
    # Check to see if sat_list is an empty list
    if not sat_list_3:
        return pd.DataFrame(), False
    
    df = pd.DataFrame({'sat_list' : sat_list_3, 'start_time' : start_time_index_3,
                       'end_time' : end_time_index_3})
    
    return df, True


# This function uses the binary search to check if a value is within the time range
def find_nearest_time(utime,target_time,time_delta):
    
    first_time = utime[0]
    end_time = utime[-1]
    
    if target_time > first_time and target_time < end_time:
        index = binary_search_index_delta(utime,0,len(utime),target_time,time_delta)
        return index
    
    return -1
    

def get_satellite_data(df,time_range,front,rear,chain_path,sub_folder):
    
    # Converts the dataframe to an array
    # Indexes are as follows:
    # 0 is satellite name
    # 1 is the start time index
    # 2 is the end time index
    df_array = df.to_numpy()
    
    # Most of this is repurposed from check 3 in identify_useable_satllites()
    
    utime = np.empty((len(df_array),0)).tolist()
    power = np.empty((len(df_array),0)).tolist()
    phase = np.empty((len(df_array),0)).tolist()
    # Check length of time range
    if len(time_range) == 1:
        # The time range covers one hour so it is easier to parse all the data
        # Finding the relevant file names for the satellites
        middle = time_range[0].strftime('%Y%m%d%H%M%S')
        file_name = front + middle + rear
        file_path = f"{chain_path}\{file_name}"
        f = h5py.File(file_path,'r')
        for i in range(len(df_array)):
            sat_path = f[df_array[i][0] + '/' + sub_folder]
            utime[i].extend(sat_path['UTC'][df_array[i][1]:df_array[i][2]])
            power[i].extend(sat_path['power'][df_array[i][1]:df_array[i][2]])
            phase[i].extend(sat_path['phase'][df_array[i][1]:df_array[i][2]])
    else:
        for time_index, time in enumerate(time_range):
            # Finding the relevant file names for the satellites
            middle = time.strftime('%Y%m%d%H%M%S')
            file_name = front + middle + rear
            file_path = f"{chain_path}\{file_name}"
            f = h5py.File(file_path,'r')
            # During the first pass we only collect data from after the start time index of the event
            if time_index == 0:
                for i in range(len(df_array)):
                    sat_path = f[df_array[i][0] + '/' + sub_folder]
                    utime[i].extend(sat_path['UTC'][df_array[i][1]:])
                    power[i].extend(sat_path['power'][df_array[i][1]:])
                    phase[i].extend(sat_path['phase'][df_array[i][1]:])
            # For any potential intermediate steps we collect data from the whole file
            # This likely should never occur as events should only a last maximum duration of 20 minutes
            elif time_index != (len(time_range)-1):
                for i in range(len(df_array)):
                    sat_path = f[df_array[i][0] + '/' + sub_folder]
                    utime[i].extend(sat_path['UTC'][()])
                    power[i].extend(sat_path['power'][()])
                    phase[i].extend(sat_path['phase'][()])
            # When we know we are taking data from the last file we want to stop at the end point of the event
            else:
                for i in range(len(df_array)):
                    sat_path = f[df_array[i][0] + '/' + sub_folder]
                    utime[i].extend(sat_path['UTC'][:df_array[i][2]])
                    power[i].extend(sat_path['power'][:df_array[i][2]])
                    phase[i].extend(sat_path['phase'][:df_array[i][2]])
                    
    df_data = pd.DataFrame({'sat_list' : df_array[:,0], 'start_time' : df_array[:,1],
                       'end_time' : df_array[:,2], 'power' : power, 'phase' : phase,
                       'UTC' : utime})
    
    return df_data
        
def main():
    
    # Amount of time in seconds allowed for difference for CERTO and CHAIN times 
    time_delta = 0.05
    
    # Location of the certo_times file
    certo_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data"
    
    # Location of the Decompressed hdf5 files
    chain_path = r"E:\vm_share\chain_data\RES\Decompressed"
    
    # Location of save directory 
    save_path = r"E:\vm_share\chain_data\chain_pickle_extract"
    
    # Change the directory
    os.chdir(certo_path)
    
    # Gather the CERTO times in utc format
    complete_path = os.path.join(certo_path, 'certo_times.txt')
    utimes = []
    with open(complete_path, 'r') as file:
        for line in file:
            currentline = line.split(",")
            utimes.append([float(currentline[0]),float(currentline[1])])
    
    # Change the directory
    os.chdir(chain_path)
    
    # First subfolder in the file
    sub_folder = 'GPS_L1CA'
    
    # File format variables
    front = 'res'
    rear = '.hdf5'
    
    # Iterate through all values in the utimes array
    for index, timestamp in enumerate(utimes):
        
        # Find the starting and ending hour for each event rounded down an hour
        start_hour = hour_floor(dt.datetime.utcfromtimestamp(timestamp[0]))
        end_hour = hour_ceiling(dt.datetime.utcfromtimestamp(timestamp[1]))
        
        # Finding how many hours each event last for to the nearest whole hour
        duration = end_hour - start_hour
        
        # Find the time range for this event
        time_range = []
        # Doing this for loop in one line created a generator object and I don't know why
        for h in range(int(duration.seconds/3600)):
            time_range.append(start_hour+dt.timedelta(hours=h))
        
        '''
        We need to perform 3 checks to ensure that the CHAIN data for each satellite is usable
        1.) Satellite exist within all time frames
            If the CERTO time covers multiple time frames we can eliminate satellites
            that only exist in one but not the other
        2.) Satellites start and end times align with CERTO
            If the satellites UTC time does not include the CERTO start or end time 
            we can eliminate it
        3.) Satellites contain continuous data
            In the event that the satellite exist within the start and end time but is 
            missing data within the time series we eliminate it
        '''
        
        df_sat, validity = identify_useable_satllites(time_range,front,rear,chain_path,sub_folder,timestamp,time_delta)
        if validity:
            
            df = get_satellite_data(df_sat,time_range,front,rear,chain_path,sub_folder)
            
            # Save dataframe to pickle
            save_file = os.path.join(save_path, 'res' + dt.datetime.utcfromtimestamp(timestamp[0]).strftime('%Y%m%d%H%M%S') + 'data.pkl')
            df.to_pickle(save_file)
        
        print('Completed timestamp ' + str(index+1) + ' of ' + str(len(utimes)))
        
        
             
if __name__=='__main__':
    main()
    