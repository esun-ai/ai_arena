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
from src import log_tool
from src.log_tool import logger
from src.utils import (
    verification_processor, 
    answer_response_processor
)
from src.publisher import Publisher
from src.subscriber import Subscriber
from src.inference import MessageOperator
from src.request_actions import post_competitors

PROJ_ID = os.environ['project_id']
TOPIC_ID = os.environ['trigger_next_topic']
SUB_ID = os.environ['gcp_sub_id']


def inference_task_handler(message):
    """
        main function for every handler subscriber pulling.
        
        parameters:
            message: message from subscriber pulling
    """
    try:
        MO = MessageOperator()
        MO.message_processer(message)
        log_msg = {}
        while MO.msg_data['retry'] >= 0:
            MO.req_data = {}
            log_msg = log_tool.logging_generator(
                MO.msg_data, MO.msg_attr
            )
            MO = post_competitors(MO, log_msg)
            log_msg = log_tool.logging_generator(
                log_msg, MO.req_data
            )
            if MO.is_verification:
                verification_processor(MO, log_msg)
            else:
                answer_response_processor(MO, log_msg)
            if MO.req_data['post_code'] == 200:
                log_msg.update({'message': f"[request_sender] break, retry: {MO.msg_data['retry']}"})
                logger.info(log_msg)
                break           
            else:
                log_msg.update({'message': f"[request_sender] retry: {MO.msg_data['retry']}"})
                logger.info(log_msg)
                MO.msg_data['retry'] = MO.msg_data['retry'] - 1
        if not MO.is_verification:
            public = Publisher(PROJ_ID, TOPIC_ID)
            public.call_gen_next(MO, log_msg)
        message.ack()
        log_msg.update({'message': f"[request_sender] message ack success!"})
        logger.info(log_msg)
    except Exception as e:
        logger.error(f"[request_sender] inference task handler error msg: {str(e)} \n")



if __name__ == '__main__':
    while True:
        try:
            sub_streaming = Subscriber(PROJ_ID, SUB_ID, inference_task_handler)
            sub_streaming.init_subscriber()
        except Exception as e:
            logger.error(f"[request_sender] While loop error msg: {e} \n")
  
