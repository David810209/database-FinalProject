from pandas_datareader import data as pdr
import pandas as pd
import yfinance as yf
import psycopg2
import psycopg2.extras as extras 
from datetime import datetime, timedelta
import time

current_time = datetime.now().strftime("%H:%M:%S")
print("Current Time =", current_time)
print("---start updating---")

conn = psycopg2.connect(
    host="finalproj-database.c2vrh8vtr5mc.us-east-1.rds.amazonaws.com",
    port=5432,
    user="postgres",
    password="a1234567890"
)

cur = conn.cursor()
#df = pd.read_csv("sandp500.csv")
sp500list = []
cur.execute("SELECT tickerid FROM Ticker;")
# display the PostgreSQL database server version
tickers = cur.fetchall()
for i in tickers:
    sp500list.append(i[0])
    #print(i[0])
    
yf.pdr_override() # <== that's all it takes :-)


for tickr in sp500list:
  # download dataframe using pandas_datareader
  today = datetime.now() + timedelta(0)
  tomorrow = today + timedelta(1)
  today = today.strftime('%Y-%m-%d')
  tomorrow = tomorrow.strftime('%Y-%m-%d')
  
  day1 = datetime.now() + timedelta(-4)
  day2 = datetime.now() + timedelta(-3)
  day1 = day2.strftime('%Y-%m-%d')
  day2 = day2.strftime('%Y-%m-%d')
  
  startdate = today
  enddate = tomorrow
  print("startdate", startdate)
  print("enddate", enddate)
  try:
    data = pdr.get_data_yahoo(tickr, start=str(startdate), end=str(enddate)).to_numpy()
    #print(data.columns)
    
    if len(data) != 0:
        data = data[0]
        if(len(data) == 0):
            continue
        #print(data)
        tickerid = tickr
        date_ = str(startdate)
        open_price = data[0]
        high_price = data[1]
        low_price = data[2]
        close_price = data[3]
        adjusted_close_price = data[4]
        volume = data[5]
        
        query = f"INSERT INTO Price(tickerid, date_, open_price, high_price, low_price, \
            close_price,adjusted_close_price,volume) \
            VALUES ('{tickerid}', '{date_}', {open_price}, {high_price}, \
            {low_price},{close_price},{adjusted_close_price},{volume}) \
            ON CONFLICT (tickerid, date_) DO UPDATE set open_price = {open_price}, \
            high_price = {high_price}, low_price = {low_price},\
            close_price = {close_price}, adjusted_close_price = {adjusted_close_price},\
            volume = {volume};"
        #print(query)
        cur.execute(query)
        #print(tickerid, date_, open_price, high_price, low_price, close_price, adjusted_close_price, volume)
  except Exception as e:
      print(e)
      pass

# close the communication with the PostgreSQL
cur.close()
conn.commit()

print("--finish updating--")
