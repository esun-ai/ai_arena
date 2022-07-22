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
from google.cloud import pubsub_v1
from src.task_wrapper import start_game, team_resend
from src.logger import logger


env = os.environ['ENV']
topic = os.environ['GENERATOR_TOPIC']
project_id = os.environ['PROJECT_ID']

db = os.environ['DB_NAME']
user = os.environ['DB_USER']
db_pass = os.environ['DB_PASS']
host = os.environ['DB_HOST']

start_topic = os.environ['START_TOPIC']
lake_topic = os.environ['LAKE_TOPIC']

# Maximum number of questions for each team
question_limit = os.environ['QUESTION_LIMIT']
rate = int(os.environ['RATE'])  # Control number of questions in start topic


def callback(message):
    """
    Pubsub callback function
    Execute start_game() or team_resend() by message attributes.
    Ack message at the end.
    """
    if message.attributes['resend']:
        team_resend(message)
    elif message.attributes['start']:
        start_game(message)
    message.ack()


def stream_pull():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        project_id, f'generator-{env}-sub')
    flow_control = pubsub_v1.types.FlowControl(max_messages=1)
    streaming_pull_future = subscriber.subscribe(
        subscription_path, callback=callback, flow_control=flow_control
    )
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()
            logger.info({'message': '[Generator] All generator task done',
                         'ENV': f'{env}'})
            pass
        except Exception as e:
            streaming_pull_future.cancel()
            logger.error({'message': '[Generator] generator task error',
                          'error_message': e,
                          'ENV': f'{env}'})
    return "All start task done"


if __name__ == '__main__':
    while True:
        try:
            stream_pull()
        except Exception as e:
            logger.error({'message': '[Generator] generator task error',
                          'error_message': e,
                          'ENV': f'{env}'})
