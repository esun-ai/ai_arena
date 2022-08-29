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

import os
from src.log_tool import logger
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError, ThreadPoolExecutor
from google.cloud.pubsub_v1.subscriber.scheduler import ThreadScheduler

NUM_MESSAGES = int(os.environ['num_message'])
MAX_WORKER = int(os.environ['max_worker'])


class Subscriber():
    """
        Define handler subscriber class
    """
    def __init__(self, proj_id, sub_id, method):
        """
            Init subscriber
            
            parameters:
                proj_id: gcp project id
                sub_id: subscription id
                method: function you want to run in callback funciton
        """
        project_id = proj_id
        subscription_id = sub_id
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_id
        )
        self.method = method
        logger.info("[request_sender] Init subscriber")


    def callback(self, message):
        """
            Function gcp subscriber will run
        """
        if message:
            try:
                logger.info("[request_sender] Subscriber callback start!")
                self.method(message)
            except Exception as e:
                logger.error("[request_sender] Subscriber callback failed!")


    def init_subscriber(self):
        """
           Start streaming subscriber
        """
        flow_control = pubsub_v1.types.FlowControl(max_messages=NUM_MESSAGES)
        scheduler = ThreadScheduler(ThreadPoolExecutor(max_workers=MAX_WORKER))
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path, callback=self.callback, flow_control=flow_control,
            scheduler=scheduler
        )
        with self.subscriber:
            try:
                logger.info(f"[request_sender] Subscriber start!")
                streaming_pull_future.result()
            except TimeoutError as e:
                logger.error(f"[request_sender] Subscriber error msg: {str(e)}")
                streaming_pull_future.cancel()
            except Exception as e:
                logger.error(f"[request_sender] Subscriber error msg: {str(e)}")
                streaming_pull_future.cancel()
