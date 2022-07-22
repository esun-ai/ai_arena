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
import requests
import argparse
import time
from google.cloud import pubsub_v1
from src.logger import logger


project_id = os.environ['PROJECT_ID']


def saitimu(service, endpoint):
    try:
        logger.info({'message': 'Start cronjob for publish teams',
                     'env': args.env})
        url = f"http://{service}{endpoint}"
        data = {'date': ''}
        res = requests.post(url, json=data)
        logger.info({'message': 'Finished cronjob for publish teams',
                     'env': args.env,
                     'status_code': str(res.status_code)})
    except Exception as e:
        logger.error({'message': 'Cronjob for publish teams failed',
                      'env': args.env,
                      'error': e})


def start():
    try:
        logger.info({'message': 'Start cronjob for start',
                     'env': args.env})
        topic = f'controller-{args.env}'
        publisher = pubsub_v1.PublisherClient()
        print(topic)
        topic_path = publisher.topic_path(project_id, topic)
        logger.info({'message': 'Start competition!!!',
                     'env': args.env})
        for i in range(5):
            publisher.publish(topic_path, 'start task'.encode('utf-8'),
                              start='YY')
        logger.info({'message': 'Finished cronjob for start',
                     'env': args.env})
    except Exception as e:
        logger.error({'message': 'Cronjob for start failed',
                      'env': args.env,
                      'error': e})


def garbage():
    try:
        logger.info({'message': 'Start cronjob for garbage',
                     'env': args.env})
        topic = f'controller-{args.env}'
        print(topic)
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic)
        publisher.publish(topic_path, 'garbage task'.encode('utf-8'),
                          garbage='YY')
        logger.info({'message': 'Finished cronjob for garbage',
                     'env': args.env})
    except Exception as e:
        logger.error({'message': 'Cronjob for garbage failed',
                      'env': args.env,
                      'error': e})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--service", help="service.namespace")
    parser.add_argument("-i", "--endpoint", help="endpoint")
    parser.add_argument("-e", "--env", help="env")
    args = parser.parse_args()
    logger.info({'message': 'Start cronjob'})
    saitimu(args.service, args.endpoint)
    time.sleep(120)
    for i in range(3):
        start()
        time.sleep(120)
