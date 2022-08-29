#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
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

import json
from src import log_tool
from src.log_tool import logger
from src.utils import (
    verification_processor, answer_response_processor
)

class MessageOperator():
    """
        Define class variables for the messages
        from subscriber pulling.
    """
    def __init__(self):
        self.msg_data = {}
        self.msg_attr = {}
        self.is_verification = None
        self.team_id = None
        self.req_data = {}


    def message_processer(self, message):
        """
            Process message from subscriber pulling.

            parameters:
                message: message from subscriber pulling
        """
        try:
            log_msg = {}
            self.msg_data = json.loads(message.data.decode('utf-8'))
            self.msg_attr = dict(message.attributes)
            self.msg_data['retry'] = int(self.msg_data['retry'])
            self.is_verification = eval(self.msg_attr.get('is_verification'))
            self.team_id = int(self.msg_attr.get('team_id'))
            log_msg = log_tool.logging_generator(
                self.msg_data, self.msg_attr, self.req_data
            )
            log_msg.update({'message': f"[request_sender] message processer success!"})
            logger.info(log_msg)

        except ValueError as e:
            log_msg.update({'message': f"""[request_sender] message processer error msg: {str(e)},
                message: {str(message)}"""})
            logger.error(log_msg)
        except Exception as e:
            log_msg.update({'message': f"""[request_sender] message processer error msg: {str(e)},
                message: {str(message)}"""})
            logger.error(log_msg)
