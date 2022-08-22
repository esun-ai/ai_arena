#!/usr/bin/env python
# -*- coding:utf-8 -*-
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
import pytest
from src.slack_event import SlackEventMessage

normal_event_dict = str(
    {
        "client_msg_id": "bab748xx-9245-4623-9cbb-0f6b1b91492f",
        "type": "message",
        "text": "verification test1@gmail.com 123456 <http://127.0.0.1:8080/>",
        "user": "U01391T2XX6",
        "ts": "1620571690.006200",
        "team": "TUJ09KNX4",
        "blocks": [
            {
                "type": "rich_text",
                "block_id": "lFgqw",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {"type": "text", "text": "verification "},
                            {
                                "type": "text",
                                "text": "test1@gmail.com",
                                "style": {"unlink": True},
                            },
                            {"type": "text", "text": " 123456 "},
                            {"type": "link", "url": "http://127.0.0.1:8080"},
                        ],
                    }
                ],
            }
        ],
        "channel": "D013UC8AXUX",
        "event_ts": "1620571690.006200",
        "channel_type": "im",
    }
)


@pytest.mark.parametrize("element, expected", [(normal_event_dict, "D013UC8AXUX")])
def test_SlackEventMessage_init(element, expected):
    slack_obj = SlackEventMessage(element)
    assert slack_obj.channel_id == expected


# def test_SlackEventMessage_no_key():
#     with pytest.raises(KeyError):
#         SlackEventMessage('{"123"}')
