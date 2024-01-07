from pandas_datareader import data as pdr
import pandas as pd
import yfinance as yf
import psycopg2
import psycopg2.extras as extras 


df = pd.read_csv("sandp500.csv")
sp500list = []
select = df[["Symbol", "Security", "GICS Sector"]]
select.rename(columns = {'Symbol':'tickerid', 'Security':'tickername', 'GICS Sector':'GICS_sector'}, inplace = True) 
print(select.columns)


#print(select)
print(len(select))

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
    cursor.close() 
  


conn = psycopg2.connect(
    host="finalproj-database.c2vrh8vtr5mc.us-east-1.rds.amazonaws.com",
    port=5432,
    user="postgres",
    password="a1234567890")

cur = conn.cursor()

cur.execute("SELECT tablename FROM pg_catalog.pg_tables where tableowner = 'postgres';")
# display the PostgreSQL database server version
db_version = cur.fetchall()
print(db_version)

execute_values(conn, select, "Ticker")


# close the communication with the PostgreSQL
cur.close()

