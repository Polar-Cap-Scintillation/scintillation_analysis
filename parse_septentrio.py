# parse_septentrio.py

from struct import *
import gzip
import numpy as np
import pandas as pd
import datetime as dt
import spacepy.time as spt
# from .utils import gps2utc

def gps2utc(wnc, tow):
    # if only a single value provided for wnc, expand to an array equal in size to tow
    # if isinstance(wnc,(int,float)):
    #     wnc = np.full(tow.shape,wnc)

    tstmp = dt.datetime(1980,1,6) + dt.timedelta(days=7.*wnc, seconds=tow)
    tm = spt.Ticktock(tstmp, 'UTC')
    utc_tstmp = tstmp-dt.timedelta(seconds=int(tm.leaps[0])-19)
    # utc_tstmp = np.array([t-dt.timedelta(seconds=(l-19.)) for t,l in zip(tstmp, tm.leaps)])
    return utc_tstmp

# def read4046(f):

#     # read time of week (ms), week #, # of satellites, length of sat info block
#     data = f.read(8)
#     tow, wnc, N, SBlength  = unpack('=IHBB', data)
#     # print('timestamp', tow, wnc)
#     # print('SBlength', N, SBlength)
#     dt_tstmp = gps2utc(wnc, tow/1000)
#     block_data = {'time_stamp':dt_tstmp}

#     # read common flags, cumulative clock jumps (ms)
#     # Note: clock jumps may be important later???
#     data = f.read(4)
#     CorrDuration, CumClkJumps, _, _ = unpack('=BBBB', data)
#     # print(CorrDuration, CumClkJumps)

#     for n in range(N):

#       # read RxChannel, type, SVID
#       data = f.read(3)
#       RxChannel, typ, svid = unpack('=BBB', data)
#       typ = typ & 0x1F
#       # print('Channel', RxChannel, typ, svid)
      
#       # read CorrIQ LSB and MSB, Carrier phase LSB
#       data = f.read(5)
#       CorrIQ_MSB, CorrI_LSB, CorrQ_LSB, CarrierPhaseLSB = unpack('=BBBH', data)
#       CorrI_MSB = CorrIQ_MSB & 0xF
#       CorrQ_MSB = CorrIQ_MSB & 0xF0

#       i = CorrI_MSB*256+CorrI_LSB
#       q = CorrQ_MSB*256+CorrQ_LSB

#       # block_data[str(svid)+'-'+str(typ)+'-I'] = i
#       # block_data[str(svid)+'-'+str(typ)+'-Q'] = q
    
#       block_data[str(svid)+'-'+str(typ)] = CarrierPhaseLSB/1000.

#     return block_data

def read4027(f):
    
#     # Read ChannelStatus Block
#     header = f.read(8)
#     sync1, sync2, crc, id0, length = unpack('=ccHHH', header)
#     # Only use first 12 bits for block ID
#     id0 = id0 & 0xfff
#     # print(sync1, sync2, crc, id0, length)
    
#     # read time of week (ms), week #, # of satellites, length of sat info block
#     data = f.read(9)
#     tow, wnc, N1, SB1length, SB2length  = unpack('=IHBBB', data)
#     print('timestamp', tow, wnc)
#     print('SBlenght', N1, SB1length, SB2length)

    # read time of week (ms), week #, # of satellites, length of sat info block
    data = f.read(9)
    tow, wnc, N1, SB1length, SB2length  = unpack('=IHBBB', data)
    # print('timestamp', tow, wnc)
    # print('SBlenght', N1, SB1length, SB2length)
    dt_tstmp = gps2utc(wnc, tow/1000)
    block_data = {'time_stamp':dt_tstmp}

    
    # read common flags, cumulative clock jumps (ms)
    # Note: clock jumps may be important later???
    data = f.read(3)
    CommonFlags, CumClkJumps, _ = unpack('=BBB', data)
    # print(CommonFlags, CumClkJumps)

    for n in range(N1):
    #   data = f.read(SB1length)

        # START READING MeasEpochChannelType1 Subblock HERE
        data = f.read(3)
        RxChannel, typ, svid = unpack('=BBB', data)
        typ = typ & 0x1F
        # print('TYPE, SVID', typ, svid)

        # BECAUSE typ = 0
        # fL = 1575.42*1.e6
        # signal type corresponds to frequency based on table
        fL = {0 : 1575.42*1.e6, 1 : 1575.42*1.e6, 2 : 1227.60*1.e6, 3 : 1227.60*1.e6, 4 : 1176.45*1.e6}

        # pseudorange (MIGHT be correct???)
        data = f.read(5)
        misc, codeLSB = unpack('=BI', data)
        codeMSB = misc & 0xF
        pseudorange = (codeMSB*4294967296+codeLSB)*0.001
        # print('pseudorange', pseudorange)

        # doppler
        data = f.read(4)
        dopp, = unpack('=i', data)
        doppler = dopp*0.0001
        # print('Doppler [Hz]', doppler)

        # carrier phase
        data = f.read(3)
        carrierLSB, carrierMSB = unpack('=Hb', data)

        lam = 299792458/fL[typ]

        carrier_phase = pseudorange/lam + (carrierMSB*65536+carrierLSB)*0.001
        # print('Carrier Phase', carrier_phase)
        block_data[str(svid)+'-'+str(typ)] = carrier_phase

        # CN0
        data = f.read(1)
        CN0, = unpack('=B', data)
        if typ in [1,2]:
            CN0 = CN0*0.25
        else:
            CN0 = CN0*0.25+10 # This equation changes depending on typ
        # print(CN0)

        # Lock time
        data = f.read(2)
        locktime, = unpack('=H', data)
        # print(locktime)

        # observation info, N2
        data = f.read(2)
        obs_info, N2 = unpack('=BB', data)
        # print(N2)

        # START READING MeasEpochChannelType2 Subblock HERE
        for i in range(N2):
            data = f.read(SB2length)
            typ2, locktime, CN0, offsetMSB, carrierMSB2, obs_info, codeoffsetLSB, carrierLSB2, doppleroffsetLSB, = unpack('=BBBBbBHHH', data)
            typ2 = typ2 & 0x1F
            CodeOffsetMSB = offsetMSB & 0x7
            DopplerOffsetMSB = offsetMSB & 0xF8
          # print('signal type', typ2)

            pseudorange2 = pseudorange + (CodeOffsetMSB*65536+codeoffsetLSB)*0.001
            lam2 = 299792458/fL[typ2]
            # print('Carrier:', carrierMSB2, carrierLSB2)
            carrier_phase2 = pseudorange2/lam2 +(carrierMSB2*65536+carrierLSB2)*0.001
            alpha = fL[typ2]/fL[typ]
          # print('Doppler Offset', DopplerOffsetMSB, doppleroffsetLSB, alpha)
            doppler2 = doppler*alpha + (DopplerOffsetMSB*65536+doppleroffsetLSB)*1e-4

      # print(pseudorange2, carrier_phase2, doppler2)
    # data = f.read(15)
    # misc, codeLSB, doppler, carrierLSB, carrierMSB, CNO, locktime = unpack('=BIiHbBH', data)
    # print(misc, codeLSB, doppler, carrierLSB, carrierMSB, CNO, locktime)


    # # read ALL SatInfo blocks
    # for i in range(N):
    #     data = f.read(SB1length)
    #     # SVID (PRN??), FreqNb (irrelevant=0), reserved, reserved, az rise/set, health status, elevation, N2, RxChannel, reserved, padding
    #     svid, fn, _, _, azrs, hs, el, N2, RxChan, _ = unpack('=BBBBHHbBBB',data)
    #     print(svid, N2, RxChan)
    #     for j in range(N2):
    #         data = f.read(SB2length)

    return block_data
    
def read_file(filename):
    df_all = list()

    with gzip.open(filename, 'rb') as f:
        while True:

            # Read Header Block
            header = f.read(8)

            # if no header, EOF, break
            if not header:
                break

            sync1, sync2, crc, id0, length = unpack('=ccHHH', header)
            # Only use first 12 bits for block ID
            id0 = id0 & 0xfff   # Block ID
            # print(sync1, sync2, crc, id0, length)


            if id0 == 4027:
                df = read4027(f)
                df_all.append(df)
            else:
                # skip block
                block = f.read(length-8)
                continue

    df = pd.DataFrame(df_all)
    df = df.set_index('time_stamp')

    return df