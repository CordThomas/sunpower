import pvlib as pv
from datetime import datetime as dt
import datetime
import sqlite3
import configparser, os
import pyowm
import pandas as pd
from solar_utils import *

config = configparser.ConfigParser()
config.read(os.path.expanduser('~/params.py'))

# The OpenWeatherMap API Key are retrieved from the OWM site
# here https://home.openweathermap.org/api_keys following registration
owm_api_key = config['OPEN_WEATHERMAP']['owm_api_key']

# Station ID is the unique identifier for a weather station of interest
# You can learn more about stations, registering them and finding
# IDs near you here:  https://openweathermap.org/stations
station_id = config['OPEN_WEATHERMAP']['own_station_id']

def send_data(conn, event_time, param, value):
   cur = conn.cursor()
   statement = 'INSERT INTO environ (tdate, ttime, param, val) VALUES (date(\'now\',\'localtime\'), ?, ?, ?)'
   cur.execute(statement, (event_time, param, value))
   conn.commit()

def get_basic_atmospheric_info(conn, event_time):
  # Initiate an API connection using your key
  owm = pyowm.OWM(owm_api_key)

  # Retrieve a weather observation from a station of interest
  observation = owm.weather_at_id(station_id)

  # An observation is largely weather information
  # combined with some collection metadata
  weather_current = observation.get_weather()

  # Weather then embodies all of the properties reported to and
  # recorded by OpenWeatherMap
  pressure_current = weather_current.get_pressure()['press']
  temp_c = weather_current.get_temperature('celsius')['temp']
  wind_speed = weather_current.get_wind()['speed']
  humidity = weather_current.get_humidity()
  sunrise = weather_current.get_sunrise_time('iso')
  sunset = weather_current.get_sunset_time('iso')
  wind_deg = weather_current.get_wind()['deg']
  cloud_cover = weather_current.get_clouds()
  wat_vap = pv.atmosphere.gueymard94_pw(temp_c, humidity)
  weather = [pressure_current, temp_c]
  # Ozone does not appear implemented yet.
  # ozone = owm.ozone_around_coords(config['OPEN_WEATHERMAP']['own_coord_lat'],
  #               config['OPEN_WEATHERMAP']['own_coord_long'])

  send_data(conn, event_time, 'pressure', pressure_current)
  send_data(conn, event_time, 'temp', temp_c)
  send_data(conn, event_time, 'wind_speed', wind_speed)
  send_data(conn, event_time, 'humidity', humidity)
  send_data(conn, event_time, 'cloud_cover', cloud_cover)
  send_data(conn, event_time, 'water_vapor', wat_vap)

  return pressure_current, temp_c

def get_solar_info(conn, datetime_now, event_time, pressure_current, temp_c):
  # Following needs to be completed - so far we've gathered
  # some metadata but have not yet calculated the expected
  # power generation yet.
  # Need to do something with airmass, weather values ?
  weather = [pressure_current, temp_c]

  # Location is used to pull solar position information
  # from NREL SOLPOS and SPECTRL2 using this Python
  # package https://pypi.org/project/SolarUtils/
  location = [config['OPEN_WEATHERMAP']['own_coord_lat'],
              config['OPEN_WEATHERMAP']['own_coord_long'],
              config['OPEN_WEATHERMAP']['own_timezone']]

  (angles, airmass) = solposAM(location, datetime_now, weather)
  zenith, azimuth = angles
  print (airmass)

  collector_altitude = config['COLLECTOR']['altitude']
  collector_tilt = config['COLLECTOR']['tilt']
  collector_azimuth = config['COLLECTOR']['azimuth']
  orientation = [collector_tilt, collector_azimuth]

  send_data(conn, event_time, 'zenith', zenith)
  send_data(conn, event_time, 'azimuth', azimuth)


def process_atmospheric():
  conn = sqlite3.connect(config['ATMOSPHERE']['db_location'])
  tm = dt.today()
  five_min = tm - datetime.timedelta(minutes=tm.minute % 5,
                                     seconds=tm.second,
                                     microseconds=tm.microsecond)

  datetime_now = [tm.year, tm.month, tm.day, tm.hour, five_min.minute, 0]
  event_time = str(tm.hour).rjust(2, '0') + ':' + str(five_min.minute).rjust(2, '0') + ':00'

  pressure_current, temp_c = get_basic_atmospheric_info(conn, event_time)
  get_solar_info(conn, datetime_now, event_time, pressure_current, temp_c)

  conn.close()

if __name__ == "__main__":
  process_atmospheric()
