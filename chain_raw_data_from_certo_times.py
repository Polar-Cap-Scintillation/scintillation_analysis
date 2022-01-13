#gather_chain_from_certo_times.py
import numpy as np
import datetime as dt
import os
from collections import OrderedDict
from chain_processing import download, extract

def hour_floor(t):
    # Rounds to earlier hour
    return (t.replace(second=0, microsecond=0, minute=0))


def hour_ceiling(t):
    # Rounds to later hour
    return (t.replace(second=0, microsecond=0, minute=0)
               +dt.timedelta(hours=1))


def run_chain_processing(dates, datadir):
    site = 'res'
    
    for date in dates:
        print(date, site)
        download(site, date, datadir)
        extract(site, date, datadir)
        
def main():
    # Location of the certo_times file
    path = r"/media/sf_VirtualboxShare/Resolute/Data"
    
    # Location of CHAIN files to save
    datadir = '/media/sf_vm_share/chain_data'
    
    # Change the directory
    os.chdir(path)
    
    # Gather the CERTO times as datetime
    complete_path = os.path.join(path, 'certo_times.txt')
    utimes = []
    with open(complete_path, 'r') as file:
        for line in file:
            currentline = line.split(",")
            starttime = dt.datetime.utcfromtimestamp(float(currentline[0]))
            endtime = dt.datetime.utcfromtimestamp(float(currentline[1]))
            utimes.append([hour_floor(starttime),hour_ceiling(endtime)])
            
    # Finding how many hours each event last for to the nearest whole hour
    duration = np.array([utimes[i][1]-utimes[i][0] for i in range(0,len(utimes))])
    
    # Finding all time ranges for aquiring CHAIN data
    dates = []
    for i in range(len(duration)):
        dates = np.append(dates,[utimes[i][0]+dt.timedelta(hours=h) for h in range(int(duration[i].seconds/3600))])
    
    # Since the dates variable will likely have duplicates in it we get rid of them to avoid creating redundant files
    setdates = list(OrderedDict.fromkeys(dates))
    
    # Place the setdates variable into the chain_processing.py file and let run for a billion years
    os.chdir(datadir)
    run_chain_processing(setdates,datadir)
    
    
if __name__=='__main__':
    main()
    