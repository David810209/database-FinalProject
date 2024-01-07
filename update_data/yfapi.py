from pandas_datareader import data as pdr
import pandas as pd
import yfinance as yf

df = pd.read_csv("sandp500.csv")
sp500list = []
for i in df["Symbol"]:
  sp500list.append(i)
print(sp500list)

yf.pdr_override() # <== that's all it takes :-)

for tickr in sp500list:
  # download dataframe using pandas_datareader
  data = pdr.get_data_yahoo(tickr, start="2000-01-01", end="2023-12-31").to_csv("history/"+tickr+'.csv')
  #print(data)