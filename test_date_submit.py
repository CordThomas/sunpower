import sqlite3

DB_LOCATION = '/Users/cthomas/Development/sunpower/atmosphere.db'

def send_data(conn, event_time, param, value):
  cur = conn.cursor()
  statement = 'INSERT INTO p_environ (tdate, ttime, param, val) VALUES (date(\'now\',\'localtime\'), ?, ?, ?)'
  cur.execute(statement, (event_time, param, value))
  conn.commit()

def test_db_send():
  conn = sqlite3.connect(DB_LOCATION)
  send_data(conn, '05:45', 'testtime', '05:45')
  conn.close()

if __name__ == "__main__":
  test_db_send()
