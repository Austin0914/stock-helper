import os
import logging
import random
import datetime
import pytz
import azure.functions as func
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

from function import stock_info
from function import database

# Initialize LINE components
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    incoming_text = event.message.text.strip()
    if "推送給所有人" in incoming_text:
        if event.source.user_id == os.environ.get('ADMIN_USER_ID'):
            send_resultToSubscribers()
        return
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
        reply_text = random.choice(stock_quotes)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

def run_stock_info():
    now_str = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d")
    computeORNOT, sendORNOT = database.get_compute_history(now_str)
    if not computeORNOT:
        company_name = stock_info.main()
        logging.info(company_name)
        if company_name and len(company_name) != 0:
            for it in company_name:
                database.add_stock(it[0], it[1], it[2], it[3], it[4])
        database.add_compute_history(now_str)
    if not sendORNOT:
        send_resultToSubscribers()
    if computeORNOT and sendORNOT:
        database.close_connection()

def send_resultToSubscribers():
    now_str = datetime.datetime.now(pytz.timezone("Asia/Taipei")).strftime("%Y-%m-%d")
    subscribers = database.get_subscribers()
    if not subscribers:
        return
    reply_text = database.get_result(now_str)
    logging.info(reply_text)
    for subscriber_id in subscribers:
        logging.info(subscriber_id[1])
        line_bot_api.push_message(
            subscriber_id[1],
            TextSendMessage(text=reply_text)
        )
    database.update_compute_history(now_str, True)
    database.close_connection()
    logging.info("成公推送給訂閱者")


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="callback")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Received a request.')
    if req.method != "POST":
        return func.HttpResponse("Method Not Allowed", status_code=405)
    signature = req.headers.get("X-Line-Signature", "")

    try:
        body = req.get_body().decode("utf-8")
    except Exception as e:
        logging.error("Error reading request body: " + str(e))
        return func.HttpResponse("Bad Request", status_code=400)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logging.error("Invalid signature.")
        return func.HttpResponse("Invalid signature", status_code=400)
    except Exception as e:
        logging.error("Error processing webhook: " + str(e))
        return func.HttpResponse("Internal Server Error", status_code=500)
    return func.HttpResponse("OK", status_code=200)

@app.timer_trigger(schedule="0 30 12 * * 1-5", arg_name="myTimer", run_on_startup=False,use_monitor=False) 
def timer_trigger(myTimer: func.TimerRequest) -> None:
    logging.info('Received a timer trigger.')
    run_stock_info()
    logging.info('Run Successfully')
'''
❓❓❓❓
1.如果我今天將這種程式部屬在azure function上面，然後我執行了os的操作他會讀取到哪一個地方呢?
    ->更基礎的問題是我不懂程式被運行的規則，什麼是伺服器?他跟我們普通電腦運行東西會不一樣嗎?
2.我今天要開發程式時，我該如何去做測試?每次都要部屬到sever才能測試?要用print嗎?還是要用log呢?
3.今天應該要如何更有效的去測試呢?只能實際部屬到雲端才能有作用嗎?像是測試linebot機器人這樣
4.今天遇到這種換伺服器的狀況導致，有很多地方需要去做測試及改變，是因為我原本程式寫得不夠好嗎?
'''