# parse_certo.py

# CERTO data
certo_data = {}

filename = '201711211837r.its'

# read header
with open(filename) as file:
    header = [next(file) for x in range(5)]

# extract file start time and data rate from header
split = header[2].split()
filestarttime = dt.datetime.strptime(split[4]+' '+split[5],'%Y-%m-%d %H:%M:%S.%f')
datarate = float(split[10])

# get TLE from 4-5 lines of header
TLE = header[3:5]

# read data from *.its file
VHFI, VHFQ, UHFI, UHFQ, _, _, _ = np.loadtxt(filename,skiprows=8,unpack=True)

# generate time array
utime = np.array([(filestarttime-dt.datetime.utcfromtimestamp(0)).total_seconds()+t/datarate for t in range(len(VHFI))])

VHF_power = VHFI**2+VHFQ**2
VHF_phase = np.unwrap(np.arctan2(VHFQ,VHFI))
UHF_power = UHFI**2+UHFQ**2
UHF_phase = np.unwrap(np.arctan2(UHFQ,UHFI))
