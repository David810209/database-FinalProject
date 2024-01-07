# 載入 json 標準函式庫，處理回傳的資料格式
import json

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
#from flask import Flask
#from flask import *
import psycopg2
import json
# from linebot.v3 import LineBotApi


from datetime import datetime

line_bot_api = LineBotApi('s/9I3T+RfFRw83YzrEl+DkWIZKu0CnyJbI/O1P7BcVslZ2zGkkQ9dYCADM486zhaHxdjxnHDAm4fc2VVxdP0CKmdsI0XYswK0u+x/gElsLbXLRPFuPOYcLHiQ1Ujcu+7VwdPgjti4UIrbV0BhZAiFgdB04t89/1O/w1cDnyilFU=')
# line_bot_api.push_message('U62903ed646b330be8dd518e64ad40328', TextSendMessage(text='peko'))


def get_today_date():
    today_date = datetime.now().date()
    formatted_date = today_date.strftime('%Y-%m-%d')
    print(today_date)
    return formatted_date
def get_db_connection():
    conn = psycopg2.connect(
        host="finalproj-database.c2vrh8vtr5mc.us-east-1.rds.amazonaws.com",
        database="postgres",
        user="postgres",
        password="a1234567890",
        port="5432"
    )
    return conn

def username_exists(username):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM user_password WHERE username = %s", (username,))
        return cur.fetchone() is not None
    finally:
        cur.close()
        conn.close()



def subscribe_query():
    conn = get_db_connection()
    current = conn.cursor()
    current.execute("select tickerid from ticker")
    all_ticker_id = current.fetchall()
    return all_ticker_id


def subscibe_notification():
    all_ticker_id = subscribe_query()
    # print(all_ticker_id)
    conn = get_db_connection()
    current = conn.cursor()
    date = '2023-12-29'
    for row in all_ticker_id:
        row_str = str(row[0])
        #print(row_str)
        current.execute("select * from price where tickerid = %s and date_  = %s", (row,date,))
        data = current.fetchone()
        open_price = data[2]
        #print(open_price)
        high_price = data[3]
        #print(high_price)
        low_price = data[4]
        #print(low_price)
        high_open = abs(high_price - open_price) / open_price
        open_low = abs(low_price - open_price) / low_price
        #print(high_open)
        #print(open_low)
        high_open_str = str(high_open)
        open_low_str = str(open_low)
        current.execute("select * from subscribe where tickerid = %s",(row))
        subscriber = current.fetchall()
        for row_sub in subscriber:
            #print(row)
            user = row_sub[1]
            percentage  = row_sub[2]
            if high_open > percentage :
                print(user, "increase")
                line_bot_api.push_message(user, TextSendMessage(text=row_str+' is increase by ' + high_open_str))
            elif open_low > percentage:
                print(user, "decrease")
                line_bot_api.push_message(user, TextSendMessage(text=row_str+' is decreasing by'+open_low_str))
            else:
                line_bot_api.push_message(user, TextSendMessage(text=row_str+' is same'))


        
        
subscibe_notification()

