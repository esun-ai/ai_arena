#!/usr/bin/env python
# Copyright (C)  E.SUN BANK
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: UTF-8 -*-
import os
import time
import hmac
import hashlib
from flask import Flask, make_response, request
from google.cloud import pubsub_v1
from src.logger import logger
from src.slack_utils import load_request_json, send_to_slack
from src.slack_bot_reply_msg import ReplyMessage
from src.pubsub_tool import PubSubOperator

# instantiate the app, and load config
app = Flask(__name__)

if os.environ["ENV"] == "prod":
    app.config.from_object("config.ProductionConfig")
elif os.environ["ENV"] == "dev":
    app.config.from_object("config.DevelopmentConfig")
else:
    app.config.from_object("config.TestConfig")
slack_signing_secret = app.config["SLACK_SIGN_SECRET"]

# Instantiates pubsub setting
project_id = app.config["PROJECT_ID"]
topic_id = f"slack-msg-{os.environ['ENV']}"

logger.info("[Slack Recipient] Service start logging...")

# Instantiates a pubsub instance
pubsub_obj = PubSubOperator(project_id, topic_id)


@app.before_request
def before_request():
    """
    判斷是否為 slack 來的 request,
    檢查 header 是否有slack 相關資訊、timestamp 是否在五分鐘之內、signature是否合格，
    任一認證失敗則回 401

    Returns:
        Response: 任一條件失敗即回 401
    """
    request_body = request.get_data(as_text=True)
    if (
        "X-Slack-Request-Timestamp" not in request.headers
        or "X-Slack-Signature" not in request.headers
    ):
        logger.warning(
            f"[Banned] Missing slack secret headers, Recieve message:{request_body}"
        )
        return make_response("", 401)
    timestamp = request.headers["X-Slack-Request-Timestamp"]
    if abs(time.time() - float(timestamp)) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        logger.warning(f"[Banned] Timeout, Recieve message:{request_body}")
        return make_response("", 401)
    sig_basestring = "v0:" + timestamp + ":" + str(request_body)
    my_signature = (
        "v0="
        + hmac.new(
            bytes(slack_signing_secret, "utf-8"),
            bytes(sig_basestring, "utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
    )
    slack_signature = request.headers["X-Slack-Signature"]
    if not hmac.compare_digest(my_signature, slack_signature):
        logger.warning(f"[Banned] Signature not match, Recieve message:{request_body} ")
        return make_response("", 401)


@app.route("/health", methods=["GET"])
def healthcheck():
    """healthcheck

    Returns:
        Response: 回覆I'm good 確認 api 活著
    """
    return make_response("I'm good", 200)


@app.route("/webhook", methods=["POST"])
def slack_webhook():
    """slack webhook呼叫點,負責處理slack event 事項

    判斷 slack request 目的,並將 user 發送的 slack messenge
    送至 pubsub topic,後回slack server

    Returns:
        response: 200 代表訊息已送至 slack topic
    """
    request_body = request.get_data(as_text=True)
    request_dict = load_request_json(request_body)

    # 初次註冊event 使用
    if "challenge" in request_dict.keys():
        return make_response(request_dict["challenge"], 200)

    # slack 來的 bot message 都會有 event key
    if "event" in request_dict.keys():
        data = request_dict["event"]

    if "bot_id" not in data and "text" in data and data["channel_type"] == "im":
        if len(data["text"]) > 1024:
            logger.warning(
                {
                    "message": f"[Banned] Someone try to send long texts : {data['text'][:1024]} from slack.",
                    "trigger": "Slack-Auth",
                    "slack_channel": data["channel"],
                    "input": data["text"][:1024],
                }
            )

            send_to_slack(
                data["channel"], data["text"][:1024], ReplyMessage.MESSAGE_TOO_LONG
            )

        else:
            logger.info(f"[Slack-Auth] Recieve message from slack:{request_body} ")
            future = pubsub_obj.publish_msg(data)
            try:
                logger.debug(
                    {
                        "message": f"[Slack] publish msg to slack topic success: msgid={future.result()} with data:{data}"
                    }
                )

            except Exception as e:
                logger.error(
                    {
                        "message": f"[Slack] publish msg to slack topic error: {e},  with data:{data}"
                    }
                )

    return make_response("msg receivied!", 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
