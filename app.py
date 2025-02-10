import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from google import genai

import stock_info  

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    incoming_text = event.message.text.strip()
    if "投信" in incoming_text:
        reply_text = f"今日符合條件的有: {', '.join(stock_info.main())}"
    else:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash", contents="給我一句在股市交易的經典名言，並且不要有任何其他的描述語句。"
        )
        reply_text = f"{response.text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)