from datetime import datetime as dt
import datetime
import sqlite3
import configparser, os
import requests

# In general, I try to keep all implementation-specific
# parameters like API keys, database passwords and local
# path-specific configurations in a config file.  Not just for
# security but to isolate the code logic from implementation
# details so as to emphasize what an individual would need
# to provide for their own effort.
# The following code would place the params.py file in
# the running context user's homedir.
config = configparser.ConfigParser()
config.read(os.path.expanduser('~/params.py'))

# PurpleAir offers an API to query your station's data.  It's a light
# weight JSON feed you can use to pull near real time data.  I pull it
# every 5 minutes and store locally.   You can pull any station's data.
# To get the ID of a station, visit PurpleAir's site and find the value
# for the query parameter detailsshowing in the URL.  I call it acct_id
# for want of a better term.
URL_PURPLE = 'https://www.purpleair.com/json?show=' + config['PURPLE']['acct_id']

# Insert a record into a param-value key pair time-based table.  The table is simply
# a date, time, param and val field.   The date is specified as today's date using
# localtime as the convention is to use UTC but i don't really like that.
def send_data(conn, event_time, param, value):
   cur = conn.cursor()
   statement = 'INSERT INTO p_environ (tdate, ttime, param, val) VALUES (date(\'now\',\'localtime\'), ?, ?, ?)'
   cur.execute(statement, (event_time, param, value))
   conn.commit()

# Simple fahrenheit to celcius conversion method
def f2c(f):
   c = (float(f) - 32) * (5/9)
   return c

# Make a get request of the PurpleAir JSON feed to post it to the
# the database.
def gather_purple():

   resp = requests.get(URL_PURPLE)
   if (resp.status_code == 200):

      conn = sqlite3.connect(config['ATMOSPHERE']['db_location'])

      data = resp.json()
      result = data['results'][0]
      pm25 = result['PM2_5Value']
      temp_c = f2c(result['temp_f'])
      humidity = result['humidity']
      pressure = result['pressure']

      tm = dt.today()
      five_min =  tm - datetime.timedelta(minutes=tm.minute % 5,
                             seconds=tm.second,
                             microseconds=tm.microsecond)
      event_time = str(tm.hour).rjust(2, '0') + ':' + str(five_min.minute).rjust(2, '0') + ':00'
 
      send_data(conn, event_time, 'pm25', pm25)
      send_data(conn, event_time, 'pressure', pressure)
      send_data(conn, event_time, 'temp', temp_c)
      send_data(conn, event_time, 'humidity', humidity)
 
      conn.close()

if __name__ == "__main__":
   gather_purple()
