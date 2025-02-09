import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import get_data  # 確認 get_data.py 在同一個資料夾下或設定好 Python 路徑

app = Flask(__name__)

# 請將下列環境變數替換成你的 LINE Channel Access Token 與 Secret
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature')
    # get request body as text
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    incoming_text = event.message.text.strip()
    if incoming_text == "投信":
        # 呼叫 get_data.py 裡的 main 函數
        # reply_text = f"今日符合條件的有:{get_data.main()}"
        reply_text = '成功讀到訊息'
    else:
        reply_text = f"未處理的訊息: {incoming_text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    app.run()