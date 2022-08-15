#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
# @Author: Guan-Yu Su
# @Date: 2022/08
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

import os
import json
from src.log_tool import logger
from google.cloud import pubsub_v1


class Publisher:
    def __init__(self, proj_id, topic_id):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(proj_id, topic_id)

    def call_gen_next(self, MO, log_msg):
        try:
            self.publisher.publish(
                self.topic_path,
                json.dumps(MO.msg_data).encode('utf-8'),
                team_id=MO.msg_attr['team_id'],
                qid=MO.msg_attr['qid'],
                slack_channel=MO.msg_attr['slack_channel'],
                is_verification=MO.msg_attr['is_verification'],
                verification_id=MO.msg_attr['verification_id'],
                team_url=MO.msg_attr['team_url'],
                start=MO.msg_attr['start'],
                esun_uuid=MO.msg_attr['esun_uuid'],
                trigger_next='Y'
            )
            log_msg.update({'message': f"[request_sender]  call_gen_next success"})
            logger.info(log_msg)
        except Exception as e:
            log_msg.update({'message': f"[request_sender]  call_gen_next failed! error msg: {str(e)}"})
            logger.error(log_msg)
