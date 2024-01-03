from flask import Flask, flash, jsonify, redirect, render_template,session,request,abort, url_for
from flask_sqlalchemy import SQLAlchemy
import psycopg2
import re
from datetime import datetime,timedelta
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
#from werkzeug.security import generate_password_hash,check_password_hash
#import psycopg2
import os

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static/"
)

#session 安全key
app.secret_key = "password"
#database資料
POSTGRES = {
    'user' : '', #你的user name
    'db' : '',#你的db名稱
    'passwd': '',#你的密碼
    'host': '' #你的db位置
}

#連線db
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{POSTGRES['user']}:{POSTGRES['passwd']}@{POSTGRES['host']}:5432/{POSTGRES['db']}'

#連線linebot
line_bot_api = LineBotApi('')#your line bot token
handler = WebhookHandler('697f344876ad1e7d4300feee9f081dfd') #your Channel secret
user_id = ''#your line userid for this linebot
line_bot_api.push_message(user_id, TextSendMessage(text='你可以開始了')) #連線成功訊息
#連線db
db = SQLAlchemy(app)

##############################line bot#############################
#連線sql query工具
conn = psycopg2.connect(dbname = POSTGRES['db'],user = POSTGRES['user'],password = POSTGRES['passwd'],host = POSTGRES['host'])

# 監聽所有來自 /webhook 的 Post Request
@app.route("/webhook", methods=['POST'])
#監聽(固定的)
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


#呈現圖片state
@app.route('/show_chart/<portfolio_id>/<startDate>')
def show_chart(portfolio_id, startDate):
    dateobj = datetime.strptime(startDate,'%Y-%m-%d').date()
    llist = []
    output_lines = []
    for i in range(30):
        cur = dateobj + timedelta(days =  i)
        cur = cur.strftime('%Y-%m-%d')
        query = f"select tickerid, ammount \
                from portfolio_ticker \
                where portfolioid = {portfolio_id}"
        cursor = conn.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
                
        total = 0.0
                
        for tickerid,ammount in res:
            price_query = f"select close_price \
                        from Price \
                    where date_ = \
                        (select max(date_) \
                        from Price \
                        where date_ <= '{cur}'  and tickerid = '{tickerid}') and tickerid = '{tickerid}';"
            cursor.execute(price_query)
            price = cursor.fetchone()
                
            if price:
                total += ammount * float(price[0])
        llist.append(total)
        output_lines.append(f"{cur},{total:.2f}")

    return render_template('show.html', rows=output_lines)

#判斷回傳訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text #接收到的字
    user_id = event.source.user_id #接收的id
    
    #輸入開始可以導到初始畫面
   #輸入任何訊息也可以跳到選單狀態
    if(re.match('開始',message)):
        
        flex_message = TextSendMessage("選擇服務項目",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="新增投資組合", text="新增投資組合")),
                                   QuickReplyButton(action=MessageAction(label="刪除投資組合", text="刪除投資組合")),
                                   QuickReplyButton(action=MessageAction(label="查詢投資組合", text="查詢投資組合")),
                                   QuickReplyButton(action=MessageAction(label="訂閱股票", text="訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="刪除訂閱股票", text="刪除訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="查詢訂閱股票", text="查詢訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="查看投資損益圖", text="查看投資損益圖"))
                               ]))
        line_bot_api.reply_message(event.reply_token, flex_message)
      
    #新增投資組合
    elif re.match('新增投資組合',message):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入您想加入投資組合的股票ID及投資股數(不限數量)\n\n格式 : 投資,股票ID_1,股數_1,股票ID_2,股數_2...(可以輸入更多)\n\n範例 : 投資,MMM,50,A,20,AAPL,500"))
    
    #新增state
    elif message.startswith('投資'):
        try:
            cur = conn.cursor() 
            parts = message.split(',')
            cur.execute("select max(portfolioid) from portfolio")
            result = cur.fetchone()
            new_portfolio_id = 1 if result[0] is None else result[0] + 1
            conn.commit()
            cur.execute("INSERT INTO portfolio (portfolioid,userid) VALUES (%s, %s)", (new_portfolio_id,user_id))
            parts = message.split(',')
            for i in range(1,len(parts),2):
                ticker_id = parts[i].strip()
                ammount = int(parts[i + 1].strip())
                cur.execute("INSERT INTO portfolio_ticker (portfolioid, tickerid,ammount) VALUES (%s, %s,%s)", ( new_portfolio_id, ticker_id, ammount))
            conn.commit()
            cur.close()
            flex_message = TextSendMessage(text="完成輸入投資!",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="查看投資結果", text="查詢投資組合")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except ValueError:
            flex_message = TextSendMessage(text="格式錯誤",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
        

    #刪除投資組合
    elif re.match('刪除投資組合',message):
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
        s = "SELECT portfolio.portfolioid,portfolio_ticker.tickerid, ammount\
                FROM portfolio LEFT JOIN portfolio_ticker \
                ON portfolio.portfolioid=portfolio_ticker.portfolioid \
                    WHERE userid = %s"
        cur.execute(s, (user_id,))
        data = cur.fetchall()
        if data:
            out = '\n'.join([str(row['portfolioid'])+":"+str(row['tickerid']) +','+str(row['ammount']) for row in data])            
        else:
            out = '你還沒有建立投資組合'
        cur.close()
        
        flex_message = TextSendMessage(text="你的投資組合:\n\n"+out+"\n"+"\n請輸入您想刪除的投資組合的ID\n\n格式 : 刪除投資,portfolio_id\n\n範例輸入 : 刪除投資, 5000",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction(label="忘記portfolio_id請按", text="查詢投資組合")),
                            ]))
        line_bot_api.reply_message(event.reply_token, flex_message)
        
    #刪除股票state
    elif message.startswith('刪除投資'):
        _, portfolio_id = message.split(',')  # 分离出股票代码
        # 数据库删除逻辑
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM portfolio_ticker WHERE portfolioid = %s", (portfolio_id))
            conn.commit()
            cur.execute("DELETE FROM portfolio WHERE portfolioid = %s", (portfolio_id))
            conn.commit()
            cur.close()
            flex_message = TextSendMessage(text="已删除投資!",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                QuickReplyButton(action=MessageAction(label="查看投資結果", text="查詢投資組合")),
                            ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
       

    #查詢投資組合
    elif re.match('查詢投資組合',message):
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) 
            s = "SELECT portfolio.portfolioid,portfolio_ticker.tickerid, ammount\
                    FROM portfolio LEFT JOIN portfolio_ticker \
                    ON portfolio.portfolioid=portfolio_ticker.portfolioid \
                        WHERE userid = %s"
            cur.execute(s, (user_id,))
            data = cur.fetchall()
            if data:
                out = '\n'.join(['Portfilio_id : '+str(row['portfolioid'])+"\nTicker_id : "+str(row['tickerid']) +'\n投資股數 : '+str(row['ammount']) +'\n' for row in data])            
            else:
                out = '你還沒有建立投資組合'
            cur.close()
            flex_message = TextSendMessage(text='你的投資組合 : \n'+ out,
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                   QuickReplyButton(action=MessageAction(label="新增投資組合", text="新增投資組合")),
                                   QuickReplyButton(action=MessageAction(label="刪除投資組合", text="刪除投資組合")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except ValueError:
            flex_message = TextSendMessage(text="查詢錯誤",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)

            
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
           
    #查看股票趨勢圖
    elif re.match('查看投資損益圖',message):                                
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入您想查詢的portfolio_id和開始日期\n\n格式 : 看圖表,portfolio_id,開使日期\n\n範例輸入 : 看圖表,1,2023-12-31"))
    
    elif message.startswith('看圖表'):
        _,portfolio_id,startDate = message.split(',')
        chart_url = url_for('show_chart', portfolio_id=portfolio_id, startDate=startDate, _external=True)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f'點擊這裡查看圖表: {chart_url}')
    )
            
            
    
    #新增訂閱股票                                                   
    elif re.match('訂閱股票',message):                                         
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入你想要訂閱的股票ID和通知百分比,\n\n格式:訂閱,股票ID,通知百分比\n\n範例輸入：訂閱,MMM,0.05"))
    
    #新增state
    elif message.startswith('訂閱'):
        try:
            _,ticker_id, percentage_str = message.split(',')
            percentage = float(percentage_str.strip())
            cur = conn.cursor() 
            cur.execute("INSERT INTO subscribe (tickerid, userid, percentage) VALUES (%s, %s, %s)", (ticker_id.strip(), user_id, percentage))
            conn.commit()
            cur.close()
            flex_message = TextSendMessage(text=f"訂閱股票 {ticker_id} 成功!",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                   QuickReplyButton(action=MessageAction(label="查詢訂閱股票", text="查詢訂閱股票")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except ValueError:
            flex_message = TextSendMessage(text="格式錯誤,請輸入股票ID和百分比,格式為:股票ID,百分比",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                   QuickReplyButton(action=MessageAction(label="查詢訂閱股票", text="查詢訂閱股票")),
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)

        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
            
    #刪除訂閱股票
    elif re.match('刪除訂閱股票',message):                                  
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入您想要刪除的股票ID\n\n格式：刪除股票,股票ID\n\n範例格式 : 刪除股票,MMM"))
        
    #刪除股票state
    elif message.startswith('刪除股票'):
        _, ticker_id = message.split(',')  # 分离出股票代码
        # 数据库删除逻辑
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM subscribe WHERE tickerid = %s AND userid = %s", (ticker_id, user_id))
            conn.commit()
            cur.close()
            flex_message = TextSendMessage(text=f"已刪除股票 {ticker_id} 的訂閱！",
                            quick_reply=QuickReply(items=[
                                QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                QuickReplyButton(action=MessageAction(label="查詢訂閱股票", text="查詢訂閱股票"))
                            ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))

    #查詢訂閱股票
    elif re.match('查詢訂閱股票',message):
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s = "SELECT ticker.tickerid, tickername,gics_sector,percentage \
                FROM subscribe LEFT JOIN ticker ON subscribe.tickerid = ticker.tickerid \
                    where userid = %s"
            cur.execute(s, (user_id,))
            data = cur.fetchall()
            if data:
                out = '\n'.join([str(row['tickerid'])+','+str(row['tickername'])+','+str(row['gics_sector'])+','+str(row['percentage']) +'\n' for row in data])
            else:
                out = '你還沒有訂閱股票'
            cur.close()
            
            flex_message = TextSendMessage(text="您已訂閱的股票 : \n\n"+out,
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                                   QuickReplyButton(action=MessageAction(label="訂閱股票", text="訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="刪除訂閱股票", text="刪除訂閱股票"))
                               ]))
            line_bot_api.reply_message(event.reply_token, flex_message)
        except ValueError:
            flex_message = TextSendMessage(text="查詢錯誤",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="回到開始選單", text="開始")),
                               ]))
            line_bot_api.reply_message(event.reply_token, TextSendMessage(flex_message))

        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(e)))
            
    else :
      #輸入任何訊息可以跳到選單狀態
        flex_message = TextSendMessage("選擇服務項目",
                               quick_reply=QuickReply(items=[
                                   QuickReplyButton(action=MessageAction(label="新增投資組合", text="新增投資組合")),
                                   QuickReplyButton(action=MessageAction(label="刪除投資組合", text="刪除投資組合")),
                                   QuickReplyButton(action=MessageAction(label="查詢投資組合", text="查詢投資組合")),
                                   QuickReplyButton(action=MessageAction(label="訂閱股票", text="訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="刪除訂閱股票", text="刪除訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="查詢訂閱股票", text="查詢訂閱股票")),
                                   QuickReplyButton(action=MessageAction(label="查看投資損益圖", text="查看投資損益圖"))
                               ]))
        line_bot_api.reply_message(event.reply_token, flex_message)
      
#前端傳訊息測試
@app.route("/send_message", methods=['POST'])
def send_message():
    text = request.form['message']
    line_bot_api.push_message(user_id, TextSendMessage(text=text))
    return render_template("test.html")

##############################line bot#############################

#################################前端#############################
#前端初始畫面
@app.route("/")
def index():
    return render_template("test.html")
#################################前端#############################

#執行linebot之類的
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
