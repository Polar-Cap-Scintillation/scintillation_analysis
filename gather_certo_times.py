#gather_certo_times.py
import datetime as dt
import os

# Taken from: https://stackoverflow.com/questions/845058/how-to-get-line-count-of-a-large-file-cheaply-in-python
def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def find_certo_file_timeframe(file_path):
    # read header
    with open(file_path) as fileheader:
        header = [next(fileheader) for x in range(5)]

    # extract file start time and data rate from header
    split = header[2].split()
    file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
    data_rate = float(split[10])
    
    # Get file length for time range
    filelen = file_len(file_path)
    
    # Find start and end time
    starttime = (file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()
    endtime = (file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()+filelen/data_rate
    utimes = (starttime,endtime)
    
    return utimes


def main():
    # Folder containing the completed certo data files
    # path = [r"/media/sf_VirtualboxShare/Resolute/2017",
    #         r"/media/sf_VirtualboxShare/Resolute/2018"]
    path = [r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2017",
            r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2018"]
    
    save_path = r"C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data"
    
    utimes = []
    for i in range(0,2):
        
        # Change the directory
        os.chdir(path[i])
        
        # Find how many files exist in directory
        files = len([file for file in os.listdir()])
        
        # Iterate through all files
        current_file = 0
        for file in os.listdir():
            current_file += 1
            file_path = f"{path[i]}/{file}"
            utimes.append(find_certo_file_timeframe(file_path))    
            print('Completed file ' + str(current_file) + ' of ' + str(files) + ' from folder ' + str(1+i) + ' of ' + str(len(path)))
        
    # Write new data to a file
    complete_name = os.path.join(save_path, 'certo_times.txt')
    
    with open(complete_name, 'w') as f:
        for item in utimes:
            f.write("%s,%s\n" % (item[0],item[1]))
    
    
if __name__=='__main__':
    main()
    