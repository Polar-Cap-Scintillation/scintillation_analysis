import datetime as dt
from pymap3d import ecef2aer, geodetic2aer
from matplotlib import pyplot as plt
from skyfield.api import EarthSatellite,load, wgs84, Topos
import pytz
import numpy as np
from sgp4.api import Satrec # pip install sgp4

# Location of Certo
resolute_bay_lat_certo = 74.72955
resolute_bay_long_certo = 360-94.90576

# Set start of file and declare utc time zone
# file_start_time = dt.datetime.strptime('2017-07-16 17:32:43.00','%Y-%m-%d %H:%M:%S.%f')
file_start_time = dt.datetime.strptime('2017-11-21 18:42:34.07','%Y-%m-%d %H:%M:%S.%f')

file_start_time_aware = file_start_time.replace(tzinfo=pytz.UTC)

# Defining the satellite
# lineelement1 = '1 39265U 13055A   17196.58905696  .00004867  00000-0  14177-3 0  9999'
# lineelement2 = '2 39265  80.9711 345.6782 0687594 170.7403 190.7263 14.23019556195558'
lineelement1 = '1 39265U 13055A   17318.45889481  .00003484  00000-0  10078-3 0  999'
lineelement2 = '2 39265  80.9715 219.4317 0682401 177.5929 182.8844 14.24201029212886'


# Creating a time array from the start time to propagate through a day in seconds
utime = [file_start_time_aware+dt.timedelta(seconds=s) for s in range(600)]
utimesgp4 = np.array([(file_start_time-dt.datetime.utcfromtimestamp(0)).total_seconds()+s for s in range(600)])

satellite = Satrec.twoline2rv(lineelement1, lineelement2)

# Convert utime from utc seconds to Timestamp to convert to julian date
# Conversion may be a few leap seconds off
jd = utimesgp4 / 86400.0 + 2440587.5

# sgp4 needs two separate variables for julian time
fr = jd % 1
jd = np.array([int(jds) for jds in jd])

# Preset list for calculation
# e will be a non-zero error code if the satellite position could not be computed for the given date.
e, r, v = satellite.sgp4_array(jd,fr)

# I don't really understand what timescale is but everything in skyfield uses it
ts = load.timescale()
satellite = EarthSatellite(lineelement1, lineelement2, 'whatname',ts)
rbo = Topos(resolute_bay_lat_certo, resolute_bay_long_certo)
time = ts.from_datetimes(utime)
el, az, rng = (satellite - rbo).at(time).altaz()

# Calculating geocentric corrdinates and assigning them to ecg
geocentric = satellite.at(ts.from_datetimes(utime))
ecg = geocentric.position.km
lat,lon =wgs84.latlon_of(geocentric)

# Calculating the elevation 
# the elevation is stored in the second row of the resulting array (azi_ele[1])
azi_ele = geodetic2aer(lat.degrees, lon.degrees, wgs84.height_of(geocentric).m, resolute_bay_lat_certo, resolute_bay_long_certo, 145, deg=True)
azi_ele2 = ecef2aer(ecg[0]*1000, ecg[1]*1000, ecg[2]*1000, resolute_bay_lat_certo, resolute_bay_long_certo, 145, deg=True)
azi_ele3 = ecef2aer(r[:,0]*1000, r[:,1]*1000, r[:,2]*1000, resolute_bay_lat_certo, resolute_bay_long_certo, 145, deg=True)

# Plotting the elevation
fig = plt.figure(figsize=(10, 4), dpi=80)
ax1 = plt.subplot2grid((1,1), (0,0))
fig.autolayout : True

# Setting the length of the axis for all plots
ax1.set(xlabel='Time [sec]',ylabel='Angle [$^0$]', title='geodetic2aer Elevation starting from 2017-11-21 18:42:34.07')
# Plotting phase data
ax1.plot(azi_ele[1])
plt.show()

fig = plt.figure(figsize=(10, 4), dpi=80)
ax1 = plt.subplot2grid((1,1), (0,0))
fig.autolayout : True

# Setting the length of the axis for all plots
ax1.set(xlabel='Time [sec]',ylabel='Angle [$^0$]', title='ecef2aer Elevation starting from 2017-11-21 18:42:34.07')
# Plotting phase data
ax1.plot(azi_ele2[1])
plt.show()

fig = plt.figure(figsize=(10, 4), dpi=80)
ax1 = plt.subplot2grid((1,1), (0,0))
fig.autolayout : True
# Setting the length of the axis for all plots
ax1.set(xlabel='Time [sec]',ylabel='Angle [$^0$]', title='ecef2aer sgp4 Elevation starting from 2017-11-21 18:42:34.07')
# Plotting phase data
ax1.plot(azi_ele3[1])
plt.show()

fig = plt.figure(figsize=(10, 4), dpi=80)
ax1 = plt.subplot2grid((1,1), (0,0))
fig.autolayout : True
# Setting the length of the axis for all plots
ax1.set(xlabel='Time [sec]',ylabel='Angle [$^0$]', title='Topos Elevation starting from 2017-11-21 18:42:34.07')
# Plotting phase data
ax1.plot(el.degrees)
plt.show()

# from propagate_tle import propagate_tle
 
# # Location of Certo
# resolute_bay_lat_certo = 74.72955
# resolute_bay_long_certo = 360-94.90576
 
# # # Set start of file and declare utc time zone
# # file_start_time = dt.datetime.strptime('2017-07-16 17:32:43.00','%Y-%m-%d %H:%M:%S.%f')
# # # file_start_time = file_start_time.replace(tzinfo=pytz.UTC)
# #
# # # Defining the satellite
# # lineelement1 = '1 39265U 13055A   17196.58905696  .00004867  00000-0  14177-3 0  9999'
# # lineelement2 = '2 39265  80.9711 345.6782 0687594 170.7403 190.7263 14.23019556195558'
 
 
# # Set start of file and declare utc time zone
# file_start_time = dt.datetime.strptime('2017-11-21 18:42:34.07','%Y-%m-%d %H:%M:%S.%f')
# # file_start_time = file_start_time.replace(tzinfo=pytz.UTC)
 
# # Defining the satellite
# lineelement1 = '1 39265U 13055A   17318.45889481  .00003484  00000-0  10078-3 0  9994'
# lineelement2 = '2 39265  80.9715 219.4317 0682401 177.5929 182.8844 14.24201029212886'
 
 
# # Creating a time array from the start time to propagate through a day in seconds
# # utime = [file_start_time+dt.timedelta(seconds=s) for s in range(86400)]
# utime = [file_start_time+dt.timedelta(seconds=s) for s in range(600)]
 
# x, y, z = propagate_tle(utime, [lineelement1, lineelement2])
 
# az, el, rng = ecef2aer(x, y, z, resolute_bay_lat_certo, resolute_bay_long_certo, 145.)
 
# # Plotting the elevation
# fig = plt.figure(figsize=(10, 4), dpi=80)
# ax1 = plt.subplot2grid((1,1), (0,0))
# fig.autolayout : True

# ax1.set(xlabel='Time [sec]',ylabel='Angle [$^0$]', title='ece2aer prop tle Elevation starting from 2017-11-21 18:42:34.07')

# ax1.plot(el)
# plt.show()