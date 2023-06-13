# parse_novatel.py

from struct import *
import gzip
import pandas as pd


def read327(f):
    
    block_data = dict()
    data = f.read(4)
    N, = unpack('=i', data)
    # print('N', N, 4+N*420)
    for _ in range(N):
        data = f.read(20)
        prn, _, tec, dtec, adr0 = unpack('=hhffd', data)
        # print('PRN', prn)
        pwr = list()
        adr = list()
        for _ in range(50):
            data = f.read(8)
            dadr, powr = unpack('=iI', data)
            adr.append(adr0+dadr/1000.)
            pwr.append(powr)
            # df_all.append({prn+'-L1-phase': adr+adr0, prn+'-L1-power': pwr})
        # f.read(8*50)
        block_data[prn] = {'phase':adr, 'power':pwr}
    f.read(4)
    
    return block_data


#     data = f.read(4)
#     N, = unpack('=i', data)
#     # print('N', N, 4+N*420)
#     for _ in range(N):
#         data = f.read(20)
#         prn, _, tec, dtec, adr0 = unpack('=hhffd', data)
#         # print('PRN', prn)
#         # print(tec, dtec)
#         pwr = list()
#         adr = list()
#         for _ in range(50):
#             data = f.read(8)
#             dadr, powr = unpack('=iI', data)
#             adr.append(adr0+dadr/1000.)
#             pwr.append(powr)
#             # df_all.append({prn+'-L1-phase': adr+adr0, prn+'-L1-power': pwr})
#         # f.read(8*50)
#         # block_data[prn] = adr

#         try:
#           power_timeseries[prn].extend(pwr)
#           phase_timeseries[prn].extend(adr)
#           tec_timeseries[prn].append(tec+dtec)
#         except KeyError:
#           power_timeseries[prn] = pwr
#           phase_timeseries[prn] = adr
#           tec_timeseries[prn] = [tec+dtec]

#     f.read(4)




def read_file(filename):

    df_all = list()
    with gzip.open(filename, 'rb') as f:

        while True:
            # Read Header Block
            header = f.read(28)

            # if no header, EOF, break
            if not header:
                break

            _, _, _, HeaderLength, MessageID, _, _, MessageLength, _, _, _, wnc, tow, _, _, _ = unpack('=BBBBHBBHHBBHLLHH', header)
            # print(HeaderLength, MessageID, MessageLength)

            if MessageID == 327:
                df = read327(f)
                # print(df)
                
                for i in range(50):
                    d = {'WNC':wnc, 'TOW':tow/1000.+i*0.02}
                    for prn, data in df.items():
                        d['phase-{:02d}-L1'.format(prn)] = data['phase'][i]
                        d['power-{:02d}-L1'.format(prn)] = data['power'][i]
                    df_all.append(d)
                    
                    
            else:
                # Skip over Block
                f.read(MessageLength+4)
    

    df = pd.DataFrame(df_all)

    return df
