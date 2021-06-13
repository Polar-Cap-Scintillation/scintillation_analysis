# -*- coding: utf-8 -*-
"""
Created on Sat Jun 12 20:25:52 2021

@author: Tate Colby
"""

from sgp4.api import Satrec # pip install sgp4
import pandas as pd
import math as ma

# tle
s = '1 39265U 13055A   17127.60173578 +.00005804 +00000-0 +16958-3 0  9993'
t = '2 39265 080.9724 057.0680 0689592 010.5592 350.9243 14.22576546185747'

satellite = Satrec.twoline2rv(s, t)

# arbitrary time for comparison
ts = pd.Timestamp(year = 2017,  month = 5, day = 7, 
                  hour = 0, minute = 0, second = 0)

# sgp4 needs two separate variables for julian time
jd = ts.to_julian_date()
fr = jd % 1
jd = ma.floor(jd)
e, r, v = satellite.sgp4(jd,fr)


print(r)  # True Equator Mean Equinox position (km)

print(v)  # True Equator Mean Equinox velocity (km/s)