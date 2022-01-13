# rename_certo_files.py
# Modified from: https://www.includehelp.com/python/copy-and-rename-files.aspx
# Importing the modules
import os
import shutil
import datetime as dt
# gets the current working dir
src_dir = [r'C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\2017',
           r'C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\2018']
# defining the dest directory
dst_dir = [r'E:\vm_share\chain_data\Resolute\2017',
           r'E:\vm_share\chain_data\Resolute\2018']

# Iterate through all files
i = 0
for paths in src_dir:
    os.chdir(paths)
    for file in os.listdir():
        data_file_path = f"{paths}\{file}"
        src_file = os.path.join(paths, file)
        shutil.copy(src_file,dst_dir[i])
        dst_file = os.path.join(dst_dir[i], file)
        
        # read header
        with open(data_file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
    
        # extract file start time and data rate from header
        split = header[2].split()
        try:
            file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S')
        # Find start time
        starttime = (file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()
        new_file_name = str(dt.datetime.utcfromtimestamp(starttime).strftime('%Y%m%d%H%M%S')) + file[-5:]
        
        new_dst_file_name = os.path.join(dst_dir[i], new_file_name)
        
        os.rename(dst_file, new_dst_file_name)
    i+=1
    
# gets the current working dir
src_dir = [r'C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2017',
           r'C:\Users\TateColby\Desktop\VirtualboxShare\Resolute\Data\2018']
# defining the dest directory
dst_dir = [r'E:\vm_share\chain_data\Resolute\Data\2017',
           r'E:\vm_share\chain_data\Resolute\Data\2018']

# Iterate through all files
i = 0
for paths in src_dir:
    os.chdir(paths)
    for file in os.listdir():
        data_file_path = f"{paths}\{file}"
        src_file = os.path.join(paths, file)
        shutil.copy(src_file,dst_dir[i])
        dst_file = os.path.join(dst_dir[i], file)
        
        # read header
        with open(data_file_path) as fileheader:
            header = [next(fileheader) for x in range(5)]
    
        # extract file start time and data rate from header
        split = header[2].split()
        try:
            file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            file_start_time = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S')
        # Find start time
        starttime = (file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()
        new_file_name = 'new' + str(dt.datetime.utcfromtimestamp(starttime).strftime('%Y%m%d%H%M%S')) + file[-5:]
        
        new_dst_file_name = os.path.join(dst_dir[i], new_file_name)
        
        os.rename(dst_file, new_dst_file_name)
    i+=1
    
