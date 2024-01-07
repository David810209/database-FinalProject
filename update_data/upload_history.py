from pandas_datareader import data as pdr
import pandas as pd
import yfinance as yf
import psycopg2
import psycopg2.extras as extras 

def execute_values(conn, df, table): 

    tuples = [tuple(x) for x in df.to_numpy()] 

    cols = ','.join(list(df.columns)) 
    # SQL query to execute 
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols) 
    cursor = conn.cursor() 
    try: 
        extras.execute_values(cursor, query, tuples) 
        conn.commit() 
    except (Exception, psycopg2.DatabaseError) as error: 
        print("Error: %s" % error) 
        conn.rollback() 
        cursor.close() 
        return 1
    print("the dataframe is inserted") 
  

df = pd.read_csv("sandp500.csv")
sp500list = []
for i in df["Symbol"]:
  sp500list.append(i)

conn = psycopg2.connect(
    host="finalproj-database.c2vrh8vtr5mc.us-east-1.rds.amazonaws.com",
    port=5432,
    user="postgres",
    password="a1234567890")

cur = conn.cursor()

#execute_values(conn, select, "Ticker")
for ticker in sp500list:
    df = pd.read_csv(f"history/{ticker}.csv")
    
    df.insert(0, "tickerid", [ticker]*len(df), True)
    df.rename(columns = {'tickerid':'tickerid', 'Date':'date_'
                         , 'Open':'open_price', 'High':'high_price',
                         'Low':'low_price','Close':'close_price',
                         'Adj Close':'adjusted_close_price','Volume':'volume',}, inplace = True) 
    execute_values(conn, df, "Price")
    #print(df.head())

# close the communication with the PostgreSQL
cur.close()

