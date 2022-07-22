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
import time
import hashlib
from google.cloud import pubsub_v1
from src.logger import logger


env = os.environ['ENV']
rate = int(os.environ['RATE'])

db = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASS']
db_host = os.environ['DB_HOST']

project_id = os.environ['PROJECT_ID']
start_topic = os.environ['START_TOPIC']
lake_topic = os.environ['LAKE_TOPIC']


def get_s_uuid(input_string):
    """
    Generate server uuid using sha256 (team_id + qid + SALT)

    Args:
        intput_str: team_id + qid + SALT

    Returns:
        hashed string
    """
    s = hashlib.sha256()
    data = (input_string).encode("utf-8")
    s.update(data)
    return s.hexdigest()


def publish_task(questions, team, start):
    """
    Publish tasks to pub/sub.
    Target topic will depend on attributes of the message

    Args
        questions(list): list of questions. Each element is python tuple: (qid, question)
        team: team id
        start:
            Y: Publish task to START topic
            else: Publish task to LAKE topic

    Returns:
        failed_task: list of faild task
          faild_task will be empty list if all tasks published successfully
    """
    topic = start_topic if start == 'Y' else lake_topic
    logger.info({'message': f'[Generator] Start publish task for team_{team}_{env}.',
                  'ENV': f'{env}'})
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic)
    failed_task = []
    running_task = []

    def callback(future):
        message_id = future.result()
        print(message_id)
    for index, question in enumerate(questions):
        q = question[1]
        qid = question[0]
        esun_uuid = get_s_uuid(f'{team}{time.time()}{qid}')
        data = '{"question":"%s","esun_uuid":"%s","retry":2}' % (q, esun_uuid)
        try:
            running_task.append(qid)
            if index % 70 == 0:
                logger.info({'message': f'[Generator] start publishing task for team_{team}_{env}: {running_task}',
                             'team_id': f'{team}',
                             'ENV': f'{env}'})
                running_task = []
            future = publisher.publish(topic_path, data.encode('utf-8'),
                                       team_id=f'{team}',
                                       team=f'team_{team}_{env}',
                                       qid=f'{qid}',
                                       is_verification='False',
                                       start=f'{start}',
                                       esun_uuid=f'{esun_uuid}')
            future.add_done_callback(callback)
        except Exception as e:
            logger.critical({'message': f'[Generator] Publish task failed for team_{team}_{env}',
                             'team_id': f'{team}',
                             'qid': f'{qid}',
                             'esun_uuid': f'{esun_uuid}',
                             'start': f'{start}',
                             'ENV': f'{env}',
                             'error': e})
            failed_task.append([qid, team, data, start, esun_uuid])

    logger.info({'message': f'[Generator] all Task: ({len(questions)}) questions published for team team_{team}_{env}.',
                  'ENV': f'{env}'})
    if failed_task:
        return failed_task
    else:
        return []


def resend_task(question):
    """
    Resend tasks to pub/sub.
    Target topic will depend on attributes of the message

    Args
        question: [qid, team, data, start, esun_uuid]

    Returns:
        True for resending success and Flase for failure
    """
    topic = start_topic if question[3] == 'Y' else lake_topic
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic)
    logger.info({'message': f'[Generator] Resend task for team_{question[1]}_{env}, q{question[0]}',
                 'team_id': question[1],
                 'qid': question[0],
                 'esun_uuid': question[4],
                 'is_verification': 'False',
                 'start': question[3],
                 'ENV': f'{env}'})
    try:
        publisher.publish(topic_path, question[2].encode('utf-8'),
                          team_id=f'{question[1]}',
                          team=f'team_{question[1]}_{env}',
                          qid=f'{question[0]}',
                          esun_uuid=f'{question[4]}',
                          is_verification='False',
                          start=f'{question[3]}')
        logger.info({'message': f'[Generator] Resned task succeeded for team_{question[1]}_{env}, q{question[0]}',
                     'team_id': question[1],
                     'qid': question[0],
                     'esun_uuid': question[4],
                     'is_verification': 'False',
                     'start': question[3],
                     'ENV': f'{env}'})
    except Exception as e:
        logger.critical({'message': f'[Generator] Resend task failed for team_{question[1]}_{env}, q{question[0]}',
                         'team_id': question[1],
                         'qid': question[0],
                         'esun_uuid': question[4],
                         'is_verification': 'False',
                         'start': question[3],
                         'ENV': f'{env}',
                         'error': e})
        return False
    return True
