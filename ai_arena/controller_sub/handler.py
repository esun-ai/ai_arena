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
import os
import json
from src.utils.logger import logger
from google.api_core.exceptions import Unknown
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError

from src.controller_base import ControllerBase

env = os.environ['ENV']

class Entrance():
    def __init__(self):
        self.project_id = os.environ['PROJECT_ID']
        self.subscriber = pubsub_v1.SubscriberClient()
        self.controller = ControllerBase()

    def callback(self, message):
        data = message.data
        attrib=message.attributes
        
        message.ack()
        if attrib['trigger_next']:
            team_id = attrib['team_id']
            qid = attrib['qid']
            team_url = attrib['team_url']
            try:
                status, msg = self.controller.trigger_next(message)
                if status:
                    logger.info(msg)
                else:
                    logger.error(msg)
            except Unknown as error:
                logger.error({'message':'[Controller] trigger next error with Unknown',
                                'error_message':str(error)})
                self.controller.re_publish(team_id,qid,team_url)
            except Exception as error:
                logger.error({'message':'[Controller] trigger next error',
                                'error_message':str(error)})
                self.controller.re_publish(team_id,qid,team_url)
        elif attrib['start']:
            try:
                status, msg = self.controller.start(message)
                if status:
                    logger.info(msg)
                else:
                    logger.error(msg)
            except Unknown as error:
                logger.error({'message':'[Controller] start competition error',
                                'error_message':str(error)})
            except Exception as error:
                logger.error({'message':'[Controller] start competition error',
                                'error_message':str(error)})

    def stream_pull(self):
        self.subscriber = pubsub_v1.SubscriberClient()
        subscription_path = self.subscriber.subscription_path(self.project_id, f'controller-{env}-sub')
        flow_control = pubsub_v1.types.FlowControl(max_messages=1)
        streaming_pull_future = self.subscriber.subscribe(
            subscription_path, callback=self.callback, flow_control=flow_control
        )
        with self.subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result()
            except TimeoutError:
                streaming_pull_future.cancel()
                logger.info({'message': '[Controller] controller task done',
                                'ENV':f'{env}'})    
                streaming_pull_future.result()
                pass
            except Exception as error:
                streaming_pull_future.cancel()
                logger.error({'message': '[Controller] controller task error',
                                'error_message': str(error),
                                'ENV':f'{env}'})    
                streaming_pull_future.result()
        return "controller task done"

if __name__ == '__main__':
    entrance = Entrance()
    while True:
        try:
            entrance.stream_pull()
        except Exception as error:
            logger.error({'message': '[Controller] controller task error',
                               'error_message': str(error),
                               'ENV':f'{env}'})    
            
