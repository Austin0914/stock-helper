import os
import random
import datetime
import pytz
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import stock_info  
import database

app = Flask(__name__)

# 請將下列環境變數替換成你的 LINE Channel Access Token 與 Secret
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

def run_stock_info():
    company_name = stock_info.main()
    print(company_name) 
    if len(company_name) != 0:
        for it in company_name:
            database.add_stock(it[0], it[1], it[2], it[3], it[4])  # 股票日期, 公司名稱, 公司代碼, 股價, 投信買超金額
    send_resultToSubscribers()

def send_resultToSubscribers():
    subscribers = database.get_subscribers()
    if not subscribers:
        return
    reply_text = database.get_result(datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d"))
    for subscriber_id in subscribers:
        line_bot_api.push_message(
            subscriber_id,
            TextSendMessage(text=reply_text)
        )
    database.close_connection()
    print("成公推送給訂閱者")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    incoming_text = event.message.text.strip()
    # if "投信" in incoming_text:
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage('獲取投信買賣超資訊中，請稍後...')
    #     )
    #     # line_bot_api.show_loading_animation(ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=60))
    #     run_stock_info(event)
    #     return 
    if "訂閱" in incoming_text:
        reply_text = '訂閱成功' if database.add_subscriber(event.source.user_id) else '訂閱失敗'
        database.close_connection()
    elif "取消" in incoming_text:
        reply_text = '取消訂閱成功' if database.delete_subscriber(event.source.user_id) else '取消訂閱失敗'
        database.close_connection()
    else:
        stock_quotes = [
            "買入時要有耐心，賣出時要有決心。—— 彼得·林奇",
            "市場永遠是對的，你的想法可能是錯的。—— 傑西·李佛摩",
            "在別人恐懼時貪婪，在別人貪婪時恐懼。—— 華倫·巴菲特",
            "不要把所有的雞蛋放在同一個籃子裡。—— 安德魯·卡內基",
            "市場是由恐懼與貪婪驅動的。—— 本傑明·葛拉漢",
            "價格是你支付的，價值是你得到的。—— 華倫·巴菲特",
            "股市的本質是不可預測的，永遠不要過度自信。—— 約翰·伯格",
            "如果你無法忍受投資價值下跌 50%，就不應該進入股市。—— 華倫·巴菲特",
            "交易並非每天都要進行，等待是交易的關鍵之一。—— 傑西·李佛摩",
            "市場短期是投票機，長期是稱重機。—— 本傑明·葛拉漢",
            "避免頻繁交易，過度交易是通往破產的捷徑。—— 彼得·林奇",
            "買股票就像買公司的一部分，而不是在買股票代號。—— 菲利普·費雪",
            "在市場低迷時，正是購買優質股票的最佳時機。—— 約翰·坦普頓",
            "成功的投資來自耐心與紀律，而非天才。—— 霍華德·馬克斯",
            "你不需要成為天才，只需避免愚蠢的錯誤。—— 查理·蒙格",
            "最大的風險是不知道自己在做什麼。—— 華倫·巴菲特",
            "過度樂觀和過度悲觀都是投資的大敵。—— 霍華德·馬克斯",
            "牛市讓人賺錢，但熊市才讓人致富。—— 史丹利·德魯肯米勒",
            "投資成功的關鍵是生存，避免賠光本金。—— 保羅·都鐸·瓊斯",
            "聰明的投資者關注風險，而不是僅僅關注回報。—— 賽斯·卡拉曼"
        ]
        reply_text = f"{random.choice(stock_quotes)}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

run_stock_info()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)