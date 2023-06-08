# chain_processing.py
# Download CHAIN high-rate data files and convert the binary files to a common hdf4 format

import numpy as np
import datetime as dt
import os
import pathlib
from tempfile import NamedTemporaryFile, TemporaryDirectory
from ftplib import FTP
import h5py
import csv
import spacepy.time as spt
from chain_credentials import *




def get_chain_sites():
    # read in CHAIN site information from table
    site_file = os.path.join(os.path.dirname(__file__), 'CHAINsites.txt')
    CHAINsites = {}
    with open(site_file, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            CHAINsites[row[1]] = {'name':row[0],'glat':float(row[2]),'glon':float(row[3]),'model':row[4]}
    return CHAINsites


def get_chain_filename(site,date):
    # form binary filename for either Novetel or Septentrio high-rate files

    CHAINsites = get_chain_sites()
    hourletters = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X']

    if CHAINsites[site]['model']=='GSV4004B':
        filename = '{:%y%m%d_%H}0000.nvd.gz'.format(date)
    else:
        filename = '{0}c{1:%j}{2}.{1:%y}_.gz'.format(site,date,hourletters[date.hour])

    return filename


def gps2utc(wnc, tow):
    # if only a single value provided for wnc, expand to an array equal in size to tow
    if isinstance(wnc,(int,float)):
        wnc = np.full(tow.shape,wnc)

    tstmp = np.array([dt.datetime(1980,1,6)+dt.timedelta(days=7.*w,seconds=t) for w,t in zip(wnc,tow)])
    tm = spt.Ticktock(tstmp, 'UTC')
    utc_tstmp = np.array([t-dt.timedelta(seconds=(l-19.)) for t,l in zip(tstmp, tm.leaps)])
    return utc_tstmp


def download(site, date, chaindatadir):

    filename = get_chain_filename(site, date)

    # localpath = pathlib.Path('/home/jovyan/mount/data/CHAIN/{}'.format(site.upper()))
    localpath = pathlib.Path(chaindatadir).joinpath(site.upper())
    if not localpath.is_dir():
        os.makedirs(localpath.joinpath('Raw'))
        os.makedirs(localpath.joinpath('Decompressed'))

    remotefile = 'gps/data/raw/{0}c/{1:%Y/%m}/{2}'.format(site,date,filename)
    localfile = localpath.joinpath('Raw',filename)

#     try:
    # with FTP('chain.physics.unb.ca') as ftp:
    with FTP('ftp.chain-project.net') as ftp:
        ftp.login(user=CHAIN_USERNAME,passwd=CHAIN_PASSWORD)

        with open(localfile, 'wb') as fp:
            ftp.retrbinary('RETR {}'.format(remotefile), fp.write)
#     except error_perm:
#         raise ValueError('No data file exists on CHAIN FTP server!')


def extract(site, date, chaindatadir):

    CHAINsites = get_chain_sites()

    filename = get_chain_filename(site, date)

    # localpath = pathlib.Path('/home/jovyan/mount/data/CHAIN/{}'.format(site.upper()))
    localpath = pathlib.Path(chaindatadir).joinpath(site.upper())
    localfile = localpath.joinpath('Raw',filename)

    # decompress file
    os.system('gunzip -k {}'.format(localfile))

    # read data from files into dictionary
    if CHAINsites[site]['model']=='GSV4004B':
        data = extract_novatel(localfile.with_suffix(''))
    else:
        data = extract_septentrio(localfile.with_suffix(''))

    # remove decompressed file
    os.remove(localfile.with_suffix(''))

    # add utc time stamp to all arrays
    for prn_data in data.values():
        for sig_data in prn_data.values():
            tstmp = gps2utc(sig_data['WNC'],sig_data['TOW'])
            sig_data['UTC'] = np.array([(t-dt.datetime.utcfromtimestamp(0)).total_seconds() for t in tstmp])


    # save to hdf5 file
    decompressedfile = localpath.joinpath('Decompressed','{}{:%Y%m%d%H%M%S}.hdf5'.format(site,date))
    with h5py.File(decompressedfile, 'w') as h5:
        for prn, prn_data in data.items():
            for sig, sig_data in prn_data.items():
                for key, value in sig_data.items():
                    h5.create_dataset('{}/{}/{}'.format(prn,sig,key), data=value)


def extract_novatel(novfile):

    # create temporary directory to save extracted text files to
    with TemporaryDirectory() as unpackdir:

        # extract text files
        system_call = '{} {} {}/'.format(os.path.join(os.path.dirname(__file__), 'parsesin/parsesin_allsvn'), novfile, unpackdir)
        os.system(system_call)

        data = {}
        for fn in os.listdir(unpackdir):
            filename = os.path.join(unpackdir,fn)

            # skip empty files
            if os.path.getsize(filename)<1:
                continue

            # read file
            with open(filename) as f:
                line = f.readline().split()
                wnc = float(line[3])

            tow, tec, adr, pwr = np.loadtxt(filename, skiprows=2, delimiter=',', usecols=(0,1,3,4), unpack=True)

            # save to dictionary
            data['G{}'.format(fn[14:16])] = {'GPS_L1CA':{'WNC':wnc,'TOW':tow,'phase':adr*2*np.pi,'power':pwr}}

    return data

def extract_septentrio(sepfile):
    # This will ONLY work if RxTools is available

    # define different signal codes
    signal_types = {0:'GPS_L1CA',3:'GPS_L2C',4:'GPS_L5',8:'GLO_L1CA',11:'GLO_L2CA',17:'GAL_L1BC',20:'GAL_E5a',21:'GAL_E5b',22:'GAL_AltBOC',24:'GEO_L1CA',25:'GEO_L5',6:'QZS_L1CA',7:'QZS_L2C', 26:'QZS_L5',28:'CMP_B1',29:'CMP_B2'}

    data = {}
    with NamedTemporaryFile() as unpackfile:

        with NamedTemporaryFile() as ismr:
            os.system('RxTools/bin/sbf2ismr -f {} -o {} -r {}'.format(sepfile,ismr.name, unpackfile.name))
            with open(ismr.name) as f:
                line = f.readline().split(',')
                wnc = float(line[0])

        tow, svid, sig, phase, I, Q = np.loadtxt(unpackfile.name, delimiter=',', unpack=True)

        # cycle through unique SVID numbers
        for svid0 in list(set(svid)):
            idx = np.argwhere(svid==svid0).flatten()
            tow0 = tow[idx]
            sig0 = sig[idx]
            phase0 = phase[idx]
            I0 = I[idx]
            Q0 = Q[idx]


            # cycle through unique signal types
            sig_dict = {}
            for sig00 in list(set(sig0)):
                idx = np.argwhere(sig00==sig0).flatten()
                sig_dict[signal_types[int(sig00)]] = {'WNC':wnc,'TOW':tow0[idx],'phase':phase0[idx]*2*np.pi,'power':I0[idx]**2+Q0[idx]**2}
            data['G{:02d}'.format(int(svid0))] = sig_dict

    return data





def main():
#     date = dt.datetime(2017,7,16,9)
    dates = [dt.datetime(2017,11,1)+dt.timedelta(hours=h) for h in range(12)]
    site = 'res'
    datadir = '/some/path'
#     download('gri',date)
#     for site in ['arc','cbb','eur','gjo','hal','kug','pon','res','tal','qik']:
#     for site in ['pon','res','tal','qik']:
    for date in dates:
        print(date, site)
        download(site, date, datadir)
        extract(site, date, datadir)
#         hdf2txt(site,date)

if __name__=='__main__':
    main()
