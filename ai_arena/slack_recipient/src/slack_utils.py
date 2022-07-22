#!/usr/bin/env python
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
# -*- coding:utf-8 -*-
import re
import json
import requests
from src.logger import logger
from config import Base


token = Base.SLACK_BOT_TOKEN
slack_url = Base.SLACK_URL


def load_request_json(request_body):
    """
    將收到的text 轉成 dictionary

    Args:
        request_body: 收到 request 的 text
    Return:
        request_dict: 將收到的 text 轉成 dictionary
    """
    request_dict = {}
    try:
        request_dict = json.loads(request_body)
    except ValueError:
        logger.warning(f"json loads error with message:{request_body}", exc_info=True)
    except:
        logger.error(f"Load Requests error:{request_body}", exc_info=True)
    return request_dict


def send_to_slack(channel, input_text, res):
    myobj = {"token": token}
    myobj["as_user"] = True
    myobj["channel"] = channel
    myobj["text"] = res
    r = requests.post(slack_url, data=myobj)
    if r.status_code == 200:
        logger.info(
            {
                "message": f"[E.SUN Reply Success!] to channel:{channel}, with input message:{input_text} , reply message:{res}",
                "trigger": "Slack-bot-reply",
                "slack_channel": channel,
                "input": input_text,
                "reply": res,
                "posted_data": myobj,
            }
        )
    else:
        logger.error(
            {
                "message": "[E.SUN Reply Failed!] to channel:{}, with input message:{} , reply message:{}".format(
                    channel, input_text, res
                ),
                "trigger": "Slack-bot-reply",
                "slack_channel": channel,
                "input": input_text,
                "reply": res,
                "posted_data": myobj,
            }
        )
