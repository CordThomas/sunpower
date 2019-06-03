from datetime import datetime, timedelta
import requests
import json
import configparser
import sqlite3
import os

URL_AUTH = 'https://monitor.us.sunpower.com/CustomerPortal/Auth/Auth.svc/Authenticate'
URL_HOURLY = 'https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getHourlyEnergyData?tokenid={0}'
URL_CURRENT = 'https://monitor.us.sunpower.com/CustomerPortal/CurrentPower/CurrentPower.svc/GetCurrentPower?id={0}'
# This API provides I parameter but that appears to be null for our system all day.
URL_POWER = 'https://monitor.us.sunpower.com/CustomerPortal/SystemInfo/SystemInfo.svc/getEnergyData?endDateTime={0}&guid={1}&interval=minute&startDateTime={2}'

def safe_val(val):
  if type(val).__name__ == 'float':
    return val
  elif type(val).__name__ == 'NoneType':
    return 'NULL'
  return val

'''
Given a DB cursor and a list of values, extract the energy produced
and used and send to database.  Sends a NULL value when there is a blank
entry in the list (such as when there is no energy produced at night.
'''
def send_data (cur, record_vals):

  sql = 'INSERT INTO sunpower (tdate, ttime, ep, eu, mp) VALUES ("{0}", "{1}", {2}, {3}, {4})'
  tdate = record_vals[0][:10]
  ttime = record_vals[0][11:]
  ep = 'NULL' if len(record_vals[1]) == 0 else record_vals[1]
  eu = 'NULL' if len(record_vals[2]) == 0 else record_vals[2]
  mp = 'NULL' if len(record_vals[3]) == 0 else record_vals[3]
  sql_state = sql.format(tdate, ttime, ep, eu, mp)
  print ('SQL: {0}'.format(sql_state))
  cur.execute(sql_state)

'''
Given a DB cursor and a dictionary object, extract the energy produced
and used and send to database.  Sends a NULL value when there is a blank
entry in the list (such as when there is no energy produced at night.
This was originally implemented to capture the URL_POWER API data with
the 'i' parameter but that's apparently null all day long for our system.
'''
def send_power_data (cur, record_vals):

  sql = 'INSERT INTO sunpower (tdate, ttime, ep, eu, mp) VALUES ("{0}", "{1}", {2}, {3}, {4})'
  tdate = record_vals['bdt'][:10]
  ttime = record_vals['bdt'][11:]
  ep = 'NULL' if 'ep' not in record_vals else safe_val(record_vals['ep'])
  eu = 'NULL' if 'eu' not in record_vals else safe_val(record_vals['eu'])
  i = 'NULL' if 'i' not in record_vals else safe_val(record_vals['i'])
  mp = 'NULL' if 'mp' not in record_vals else safe_val(record_vals['mp'])
  sql_state = sql.format(tdate, ttime, ep, eu, mp)
  cur.execute(sql_state)

'''
Get the entire history of data on an hourly basis since the beginning of time.
Used this originally to seed the database since the beginning of production.
Could go back and use the getEnergyData for daily 5-minute increments if i want
the granularity, but for now, hourly is fine as I simply want to compare gross
production and consumption.  Moving forward will use to compare production
to environmental conditions and consumption to occupancy conditions.
'''
def get_hourly(cur, auth_token):

  r = requests.get(URL_HOURLY.format(auth_token))

  hourly_data = r.json()['Payload']
  hourl_data_dict = hourly_data.split('|')
  for hourly in hourl_data_dict:
    send_data (cur, hourly.split(','))

def get_auth_token():
  headers = {
     'Accept': 'application/json',
     'Content-Type': 'application/json; charset=utf-8'
  }

  config = configparser.ConfigParser()
  config.read(os.path.expanduser('~/params.py'))

  body = {
    'isPersistent': config.getboolean('SUNPOWER', 'isPersistent'),
    'password': config['SUNPOWER']['password'],
    'username': config['SUNPOWER']['username']
  }

  r = requests.post(URL_AUTH, data=json.dumps(body), headers=headers)

  if (r.status_code == 200):
    auth_resp = r.json()
    print('response {0}'.format(auth_resp))
    token =  auth_resp['Payload']['TokenID']

    return token

  return "error"

def get_current(auth_token):

  r = requests.get(URL_CURRENT.format(auth_token))

  print (r.status_code)
  print (r.text)

'''
Get the power every hour and send to local database.
For now this handles lookbacks by month, but not yet by
year which I will include next.  This records the power
production and consumption for the hour starting 2 hours 
ago, so it has to make calculations when that hour was.
I am sure there are more pythonic ways to do this using some
sort of datediff method i will learn about later.  For now
it's just fun thinking about the math.
'''
def get_power(cur, auth_token):

  '''
  time, start, end
  0, 22, 23
  1, 23, 24
  2, 0, 1
  '''
  power_date_time_hour = datetime.now().replace(microsecond=0,second=0,minute=0)
  power_date_time_start = power_date_time_hour - timedelta(hours = 2)
  power_date_time_end = power_date_time_start.replace(minute=55)
  '''  print ("Start {0} and End {1}".format(
    power_date_time_start.strftime('%Y-%m-%dT%H:%M:%S'),
    power_date_time_end.strftime('%Y-%m-%dT%H:%M:%S'))) '''

  r = requests.get(URL_POWER.format(power_date_time_end, auth_token,power_date_time_start))
  hourly_data = r.json()['Payload']['series']['data']
  for five_min in hourly_data:
    print("      Dict data {0}".format(five_min))
    send_power_data (cur, five_min)

def process_sunpower():
  conn = sqlite3.connect('/mnt/usb1/sunpower/environ.db')
  cur = conn.cursor()

  auth_token = get_auth_token()

  if (auth_token != "error"):
#    get_hourly(cur, auth_token)
    get_power(cur, auth_token)

  conn.commit()
  conn.close()

if __name__ == "__main__":
  process_sunpower()