from pandas_datareader import data as pdr
import pandas as pd
import yfinance as yf
import psycopg2
import psycopg2.extras as extras 
from datetime import datetime, timedelta


conn = psycopg2.connect(
    host="finalproj-database.c2vrh8vtr5mc.us-east-1.rds.amazonaws.com",
    port=5432,
    user="postgres",
    password="a1234567890"
)

cur = conn.cursor()
sp500list = []
cur.execute("SELECT tickerid FROM Ticker;")
# display the PostgreSQL database server version
tickers = cur.fetchall()
for i in tickers:
    sp500list.append(i[0])
    #print(i[0])
    
yf.pdr_override() # <== that's all it takes :-)

for tickr in sp500list:
    # Get the data of the stock
    apple_stock = yf.Ticker(tickr)
    #print(apple_stock.history(period='5m', interval='1m')['Close'][-1])
    value = pdr.get_data_yahoo(tickr, period='1m', interval='1m')['Close'][-1]
    #value = apple_stock.history(period='1m', interval='1m')['Close'][-1]
    print(tickr, value)
    
    query = f"INSERT INTO live_price(tickerid, currentprice) \
            VALUES ('{tickr}', {value}) \
            ON CONFLICT (tickerid) DO UPDATE set currentprice = {value};"
    cur.execute(query)
    
# close the communication with the PostgreSQL

conn.commit()
cur.close()


