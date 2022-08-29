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
import json
import time
from psycopg2 import sql
from google.cloud import pubsub_v1
from src.db_tools import DBOperator
from src.pubsub_tools import publish_task, resend_task, get_s_uuid
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


def update_status_sql(status, team_id, date):
    """
    Generate sql string to update state of question generation for each team
    Args:
        status: status corresponding to question generation process
        team_id: team id
        date: game date
    Returns:
        sqlstring: sql string to be executed
    """
    if team_id:
        sqlstring = sql.SQL(
            """
                    UPDATE generator_status
                    SET insert_question_status = {status}
                    WHERE team_id = {team_id} AND send_date::timestamp::date = {date}
                    AND insert_question_status = {last_status}
                    RETURNING team_id
                    """
        ).format(status=sql.Literal(status), team_id=sql.Literal(team_id),
                 date=sql.Literal(date), last_status=sql.Literal(status - 1))
    else:
        sqlstring = sql.SQL(
            """
                    UPDATE generator_status
                    SET insert_question_status = {status}
                    WHERE send_date::timestamp::date = {date}
                    AND insert_question_status = {last_status}
                    RETURNING team_id
                    """
        ).format(status=sql.Literal(status), date=sql.Literal(date), last_status=sql.Literal(status - 1))
    return sqlstring


def get_team_url_sql(team_id):
    """
    Generate sql string to get team's verified api url
    Args:
        team_id: team id
    Returns:
        sqlstring: sql string to be executed
    """
    sqlstring = sql.SQL("""
                        SELECT b.api_url
                        FROM (
                        SELECT team_id, MAX(verification_time) AS ver_time
                        FROM public.verification
                        WHERE status_code_infer = 200 AND team_id = {team_id}
                        GROUP BY team_id) a
                        INNER JOIN
                          (
                           SELECT team_id, verification_time, api_url
                           FROM public.verification) b ON a.team_id = b.team_id AND a.ver_time = b.verification_time
                        """
                        ).format(team_id=sql.Literal(team_id))
    return sqlstring


def get_questions_sql(date, question_limit):
    """
    Generate sql string to get all questions in specific date
    Args:
        date: send_date in questions table
    Returns:
        sqlstring: sql string to be executed
    """
    if question_limit:
        limit = int(question_limit)
        sqlstring = sql.SQL("""SELECT qid, question
                               FROM questions
                               WHERE send_date = {date}
                               LIMIT {limit}""").format(date=sql.Literal(date), limit=sql.Literal(limit))
    else:
        sqlstring = sql.SQL("""SELECT qid, question
                               FROM questions
                               WHERE send_date = {date}""").format(date=sql.Literal(date))
    return sqlstring


def team_resend(message):
    """
    Resend questions for specific team.
    Args:
        message: Pubsub message.
    """
    question_dict = json.loads(message.data.decode('utf-8'))
    print(question_dict)
    team_id = message.attributes['team_id']
    try:
        db_operator = DBOperator()
        sql_string = sql.SQL("""
                             SELECT qid, question
                             FROM questions
                             WHERE qid in {qid_list}
                             """).format(qid_list=sql.Literal(tuple(question_dict['qid'])))
        logger.info({'message': f'[Generator] Get resend task for team_{team_id}',
                     'ENV': f'{env}'})
        questions = db_operator.execute_sql_with_return(sql_string)
        message.ack()
    except Exception as e:
        logger.error({'message': f'[Generator] Get resend task for team_{team_id} error: {e}',
                      'ENV': f'{env}'})
        questions = []
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, lake_topic)
    failed_task = []
    logger.info({'message': f'[Generator] Get resend task for team_{team_id} with {len(questions)} tasks',
                 'ENV': f'{env}'})
    for question in questions:
        q = question[1]
        qid = question[0]
        esun_uuid = get_s_uuid(f'{team_id}{time.time()}{qid}')
        data = '{"question":"%s","esun_uuid":"%s","retry":2}' % (q, esun_uuid)
        try:
            publisher.publish(topic_path, data.encode('utf-8'),
                              team_id=f'{team_id}',
                              team=f'team_{team_id}_{env}',
                              qid=f'{qid}',
                              is_verification='False',
                              start='N',
                              esun_uuid=f'{esun_uuid}')
        except Exception as e:
            logger.critical({'message': f'[Generator] Publish task failed for team_{team_id}_{env}',
                             'team_id': f'{team_id}',
                             'qid': f'{qid}',
                             'esun_uuid': f'{esun_uuid}',
                             'start': 'N',
                             'ENV': f'{env}',
                             'error': e})
            failed_task.append([qid, team_id, data, 'N', esun_uuid])
    if failed_task:
        for i in failed_task:
            resend_task(i)

    logger.info({'message': f'[Generator] Resend task for team_{team_id}',
                 'ENV': f'{env}'})

    s = get_team_url_sql(team_id)
    try:
        db_operator = DBOperator()
        team_url = db_operator.execute_sql_with_return(s)
    except Exception as e:
        team_url = ''
        logger.error({'message': f'[Generator] Get team url for team_{team_id} failed',
                      'ENV': f'{env}',
                      'error': e})
    if team_url:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, f'controller-{env}')
        try:
            for i in range(rate):
                publisher.publish(topic_path, 'resend'.encode('utf-8'),
                                  team_id=f'{team_id}',
                                  team_url=f'{team_url[0][0]}',
                                  qid='1313',
                                  trigger_next='Y')
            logger.info({'message': f'[Generator] trigger next for team_{team_id}_{env}',
                         'team_id': f'{team_id}',
                         'ENV': f'{env}'})
        except Exception as e:
            logger.critical({'message': f'[Generator] trigger next failed for team_{team_id}_{env}',
                             'team_id': f'{team_id}',
                             'ENV': f'{env}',
                             'error': e})


def start_game(message):
    """
    Generator work flow when game start
    Args:
        message: pub/sub message for trigger. Attributes include team_id, start and date
    """
    logger.info(f"Received {message.data}.")
    team_id = message.attributes['team_id']
    date = message.attributes['date']

    logger.info({'message': f'[Generator] get team_{team_id}_{env}',
                 'team_id': str(team_id),
                 'date': str(date),
                 'ENV': f'{env}'})
    try:
        db_operator = DBOperator()
        sql_get_questions = get_questions_sql(date, question_limit)
        questions = db_operator.execute_sql_with_return(sql_get_questions)
        sql_update_status = update_status_sql(2, team_id, date)
        db_operator.execute_sql_with_return(sql_update_status)
        message.ack()
        logger.info({'message': f'[Generator] Get {len(questions)} questions from DB',
                      'team_id': str(team_id),
                      'date': str(date),
                      'ENV': f'{env}'})
    except Exception as e:
        logger.error({'message': f'[Generator] update db error {e}',
                      'team_id': str(team_id),
                      'date': str(date),
                      'ENV': f'{env}'})
        raise e
    logger.info({'message': f'[Generator] start publish task for team_{team_id}_{env}',
                  'team_id': str(team_id),
                  'date': str(date),
                  'ENV': f'{env}'})
    start_f = publish_task(questions[:rate], team_id, 'Y')
    last_f = publish_task(questions[rate:], team_id, 'N')
    if start_f or last_f:
        logger.info({'message': f'[Generator] Find failed tasks. start: {len(start_f)}, rest: {len(last_f)}'})
        for i in start_f + last_f:
            resend_task(i)
    else:
        logger.info({'message': f'[Generator] all task for team_{team_id}_{env} published',
                      'team_id': str(team_id),
                      'date': str(date),
                      'ENV': f'{env}'})
    try:
        db_operator = DBOperator()
        sql_update_status = update_status_sql(3, team_id, date)
        db_operator.execute_sql_with_return(sql_update_status)
    except Exception as e:
        logger.error({'message': f'[Generator] update db error {e}',
                      'team_id': str(team_id),
                      'date': str(date),
                      'ENV': f'{env}'})
        raise e
