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

# from slack_vm_utils import extract_email
import json
import re
import ast


class SlackEventMessage(object):
    """
    Slack_event_message 將接到的 slack event 打包成 object


    Args:
        object (_type_): _description_
    """

    def __init__(self, slack_event_text):
        """
        根據slack 給定的 key 設定object value
        """
        # replace
        text_from_slack = slack_event_text.replace("\\xa0", " ")  # restore space string
        print("--------------------")
        slack_dict = ast.literal_eval(text_from_slack)
        print(slack_dict)
        print("--------------------")

        self.source_dict = slack_dict  # keep json data from slack in this var
        self.slack_status = 0

    @property
    def slack_msg_id(self):
        return self.source_dict["client_msg_id"]

    @property
    def channel_id(self):
        return self.source_dict["channel"]

    @property
    def user(self):
        return self.source_dict["user"]

    @property
    def text_msg_list(self):
        text_msg = self.source_dict["text"].split(" ")
        return text_msg

    @property
    def channel_type(self):
        if self.source_dict["event"]["channel_type"] != "im":
            print("channel source is not im !!")
        return self.source_dict["event"]["channel_type"]

    @property
    def is_user(self):
        if "bot_id" in self.source_dict["event"]:
            return False
        else:
            return True

    @property
    def user_purpose(self):
        command = self.text_msg_list[0].lower()
        if command not in [
            "forget_token",
            "register",
            "verification",
            "get_status",
            "get_log",
        ]:
            self.slack_status = 8
            return "unknown_command"
        else:
            return command
