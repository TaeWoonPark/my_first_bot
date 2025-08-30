import os
import re
from datetime import datetime
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ReplyMessageRequest,
    Configuration,
    MessagingApi,
)
from linebot.v3.messaging.models import (
    TextMessage,
    FlexMessage,
    QuickReply,
    QuickReplyItem,
    PostbackAction,
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)

# LINE Bot SDK v3の設定
configuration = Configuration(access_token=os.environ["ACCESS_TOKEN"])
line_bot_api = MessagingApi(configuration)
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


@app.route("/")
def index():
    return "You call index()"


@app.route("/callback", methods=["POST"])
def callback():
    """Messaging APIからの呼び出し関数"""
    # LINEがリクエストの改ざんを防ぐために付与する署名を取得
    signature = request.headers["X-Line-Signature"]
    # リクエストの内容をテキストで取得
    body = request.get_data(as_text=True)
    # ログに出力
    app.logger.info("Request body: " + body)

    try:
        # signature と body を比較することで、リクエストがLINEから送信されたものであることを検証
        handler.handle(body, signature)
    except InvalidSignatureError:
        # クライアントからのリクエストに誤りがあったことを示すエラーを返す
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    recieved_message = event.message.text

    # 腸活アンケートの開始キーワードをチェック
    if "腸活" in recieved_message or "アンケート" in recieved_message or "健康" in recieved_message:
        send_health_survey(event.reply_token)
    else:
        # 通常のメッセージ処理
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y年%m月%d日 %H時%M分%S秒")

        send_message = (
            f"{recieved_message}\n\n受信時刻: {formatted_time}\nヤーコン！凄い！美味しい！「腸活最高」"
        )

        # v3での返信方法
        request_body = ReplyMessageRequest(
            reply_token=event.reply_token, messages=[TextMessage(text=send_message)]
        )
        line_bot_api.reply_message(request_body)


@handler.add(PostbackEvent)
def handle_postback(event):
    """ポストバックイベントの処理（アンケート回答）"""
    data = event.postback.data

    if data.startswith("survey_"):
        handle_survey_response(event.reply_token, data)
    elif data == "learn_more":
        send_yacon_info(event.reply_token)


def send_health_survey(reply_token):
    """腸活アンケートを送信"""
    flex_message = FlexMessage(
        alt_text="腸活に関するアンケートです",
        contents={
            "type": "bubble",
            "size": "kilo",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🌱 腸活アンケート",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#27AE60",
                    }
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "あなたの腸活への関心度を教えてください",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                    },
                    {
                        "type": "text",
                        "text": "腸活は健康の基本！毎日の生活に取り入れていますか？",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#27AE60",
                        "action": {
                            "type": "postback",
                            "label": "とても関心がある",
                            "data": "survey_high_interest",
                        },
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "少し関心がある",
                            "data": "survey_medium_interest",
                        },
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "postback",
                            "label": "あまり関心がない",
                            "data": "survey_low_interest",
                        },
                    },
                ],
            },
        },
    )

    # v3での返信方法
    request_body = ReplyMessageRequest(reply_token=reply_token, messages=[flex_message])
    line_bot_api.reply_message(request_body)


def handle_survey_response(reply_token, data):
    """アンケート回答の処理"""
    if "high_interest" in data:
        message = "素晴らしいです！腸活への関心が高いですね！\n\nヤーコンは腸活に最適な食材です。食物繊維が豊富で、腸内環境を整える効果があります。"
        quick_reply = QuickReply(
            items=[QuickReplyItem(action=PostbackAction(label="ヤーコンについて詳しく", data="learn_more"))]
        )

        # v3での返信方法
        request_body = ReplyMessageRequest(
            reply_token=reply_token, messages=[TextMessage(text=message, quick_reply=quick_reply)]
        )
        line_bot_api.reply_message(request_body)

    elif "medium_interest" in data:
        message = "腸活に少し関心があるのですね！\n\nヤーコンを始めてみませんか？自然な甘さで、お料理にも使いやすい食材です。腸活の第一歩としておすすめです！"
        quick_reply = QuickReply(
            items=[QuickReplyItem(action=PostbackAction(label="ヤーコンについて詳しく", data="learn_more"))]
        )

        # v3での返信方法
        request_body = ReplyMessageRequest(
            reply_token=reply_token, messages=[TextMessage(text=message, quick_reply=quick_reply)]
        )
        line_bot_api.reply_message(request_body)

    elif "low_interest" in data:
        message = "腸活に興味がないのですね。でも、健康な体づくりは大切です。\n\nヤーコンは美味しくて栄養豊富。まずは食べてみることから始めてみませんか？"
        quick_reply = QuickReply(
            items=[QuickReplyItem(action=PostbackAction(label="ヤーコンについて詳しく", data="learn_more"))]
        )

        # v3での返信方法
        request_body = ReplyMessageRequest(
            reply_token=reply_token, messages=[TextMessage(text=message, quick_reply=quick_reply)]
        )
        line_bot_api.reply_message(request_body)


def send_yacon_info(reply_token):
    """ヤーコンの詳細情報を送信"""
    flex_message = FlexMessage(
        alt_text="ヤーコンについて詳しく説明します",
        contents={
            "type": "bubble",
            "size": "giga",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "🥔 ヤーコンについて",
                        "weight": "bold",
                        "size": "lg",
                        "color": "#8B4513",
                    }
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "ヤーコンの魅力",
                        "weight": "bold",
                        "size": "md",
                        "color": "#8B4513",
                    },
                    {
                        "type": "text",
                        "text": "• 食物繊維が豊富で腸活に最適\n• 自然な甘さで料理に使いやすい\n• 低カロリーでダイエットにも効果的\n• ビタミン・ミネラルが豊富",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                    },
                    {
                        "type": "text",
                        "text": "おすすめの食べ方",
                        "weight": "bold",
                        "size": "md",
                        "color": "#8B4513",
                        "margin": "lg",
                    },
                    {
                        "type": "text",
                        "text": "• 生のままサラダに\n• 炒め物や煮物に\n• スムージーやジュースに\n• お菓子作りにも活用",
                        "wrap": True,
                        "color": "#666666",
                        "size": "sm",
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "ヤーコン！凄い！美味しい！「腸活最高」",
                        "color": "#27AE60",
                        "weight": "bold",
                        "align": "center",
                    }
                ],
            },
        },
    )

    # v3での返信方法
    request_body = ReplyMessageRequest(reply_token=reply_token, messages=[flex_message])
    line_bot_api.reply_message(request_body)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
