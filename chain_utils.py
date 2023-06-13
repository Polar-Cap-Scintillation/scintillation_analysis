import datetime as dt
import csv
import os
import requests
import pandas as pd
import spacepy.time as spt
import numpy as np

import parse_novatel
import parse_septentrio


def gps2utc(wnc, tow):
    # if only a single value provided for wnc, expand to an array equal in size to tow
    # if isinstance(wnc,(int,float)):
    #     wnc = np.full(tow.shape,wnc)
    
    # tstmp = np.datetime64('1980-01-06') + wnc.astype('timedelta64[W]') + (tow*1000.).astype('timedelta64[ms]')
    # tm = spt.Ticktock(tstmp.astype('datetime64[s]').astype(int), 'UNX')
    # utc_tstmp = tstmp-(tm.leaps.astype('timedelta64[s]')-19)

    tm = spt.Ticktock(wnc*7*24*60*60+tow, 'GPS')
    utc_tstmp = np.array(tm.UTC, dtype='datetime64')
    
    return utc_tstmp



class DataManager(object):
    def __init__(self, data_dir='data/CHAIN'):

        self.chain_data_dir = data_dir
        
        # will need to change this to use importlib when packaging
        site_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CHAINsites.txt')
        self.load_site_info(site_file)
        
    def load_site_info(self, site_file):
        # read in CHAIN site information from table
        CHAINsites = {}
        with open(site_file, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                CHAINsites[row[1]] = {'name':row[0],'glat':float(row[2]),'glon':float(row[3]),'model':row[4]}
        self.chain_site_info = CHAINsites

    def form_filename(self, site, time):
        # form binary filename for either Novetel or Septentrio high-rate files

        hourletters = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X']

        if self.chain_site_info[site]['model']=='GSV4004B':
            filename = '{:%y%m%d_%H}0000.nvd.gz'.format(time)
        else:
            filename = '{0}c{1:%j}{2}.{1:%y}_.gz'.format(site, time, hourletters[time.hour])

        filepath = os.path.join(self.chain_data_dir, site, filename)
        
        return filepath

    def download(self, site, time):

        filename = self.form_filename(site, time)
        fpath, fname = os.path.split(filename)
        
        # create data directory path if it doesn't exist
        if not os.path.isdir(fpath):
            os.makedirs(fpath)
        
        # download file from CHAIN website
        url = 'http://www.chain-project.net/data/gps/data/raw/{0}c/{1:%Y/%m}/{2}'.format(site, time, fname)
        resp = requests.get(url)
        print('DOWNLOADING {}'.format(url))
        with open(filename, 'wb') as f:
            f.write(resp.content)

    def retrieve_data(self, site, starttime, endtime):

        # get hours for this interval
        total_hours = int((endtime.replace(minute=0, second=0)-starttime.replace(minute=0, second=0))/dt.timedelta(hours=1))+1
        hours = [starttime.replace(minute=0, second=0) + dt.timedelta(hours=h) for h in range(total_hours)]
        
        frames = list()
        for hr in hours:
            filename = self.form_filename(site, hr)
            print(hr, filename)
            
            if not os.path.isfile(filename):
                self.download(site, hr)

            if self.chain_site_info[site]['model'] == 'GSV4004B':
                frame = parse_novatel.read_file(filename)
            else:
                frame = parse_septentrio.read_file(filename)

            frames.append(frame)

        data = pd.concat(frames)
        
        # add UTC timestamp to dataframe
        data = data.assign(time_stamp=gps2utc(data['WNC'], data['TOW']))
        data = data.set_index('time_stamp')
        # shorten dataframe to only times of interest
        data = data.loc[starttime.strftime('%Y-%m-%d %H:%M:%S.%f'):endtime.strftime('%Y-%m-%d %H:%M:%S.%f')]

        return data