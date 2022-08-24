# -*- coding:utf-8 -*-
# Copyright (C) 2022  E.SUN BANK.
# @Author: Hsin-Hsien Ho
# @Date: 2022/07
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
import pandas as pd
from datetime import datetime
from google.cloud import monitoring_v3, pubsub_v1
from google.cloud.monitoring_v3 import query
from src.slack_utils import get_conn
from src.logger import logger

monitor_client = monitoring_v3.MetricServiceClient()

class Check_End_Signal(object):
    """
    Check if we can activate Leaderboard.
    """
    def __init__(self, now_timestamp):
        self.timestamp = now_timestamp.strftime('%Y-%m-%d')
        self.project = os.environ['GCP_PROJECT']
        self.resource_type = 'pubsub_subscription'
        self.env = os.environ['ENV']
        self.sub_name_list = [os.environ['START_SUB'], os.environ['SEA_SUB']]
        self.topic_id = f'generator-{self.env}'
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project, self.topic_id)
        with get_conn() as conn:
            self.get_q_num(conn)
            self.get_verified_list(conn)
        if self.q_num == 0:
            logger.error({
                "message": "[Leaderboard] No existing question at {}.".format(self.timestamp),
                "trigger": "Leaderboard",
                "ENV": self.env
            })
            raise ValueError("No existing question at {}.".format(self.timestamp))

    def check_pubsub_empty(self):
        """
        Check if pubsub is empty or not.

        Return:
            - True: pubsub is empty
            - False: pubsub is not empty
        """
        while True:
            try:
                result = query.Query(
                    monitor_client,
                    self.project,
                    'pubsub.googleapis.com/subscription/num_undelivered_messages',
                    end_time = datetime.now(),
                    minutes=1).as_dataframe()
                logger.info({
                        "message": f"[Leaderboard] result: {result}",
                        "trigger": "Leaderboard",
                        "ENV": self.env,
                        "timestamp": str(datetime.now())})
                if result.empty:
                    logger.info({
                        "message": f"[Leaderboard] result is empty",
                        "trigger": "Leaderboard",
                        "ENV": self.env,
                        "timestamp": str(datetime.now())})
                    time.sleep(5)
                    continue
                count_list = []
                logger.info({
                        "message": f"[Leaderboard] sub_name_list: {self.sub_name_list}",
                        "trigger": "Leaderboard",
                        "ENV": self.env,
                        "timestamp": str(datetime.now())})
                for name in self.sub_name_list:
                  val = int(result[('pubsub_subscription', self.project, name)])
                  if val > 0:
                    logger.info({
                        "message": f"[Leaderboard] subscription {name} still has {val} messages",
                        "trigger": "Leaderboard",
                        "ENV": self.env,
                        "timestamp": str(datetime.now())})
                  count_list.append(val)
                count_list = [int(result[('pubsub_subscription', self.project, name)])
                                  for name in self.sub_name_list]
                break
            except Exception as error:
                logger.warning({
                    "message": f"[Leaderboard] check_pubsub_empty error: {error}",
                    "trigger": "Leaderboard",
                    "ENV": self.env,
                    "timestamp": str(datetime.now())})
                time.sleep(5)
        print(count_list)
        return sum(count_list) == 0

    def resend_question(self, team_id, q_id_list):
        """
        Resend question to Generator if we missed the team.
        (the self.topic_path is Generator)

        Parameters:
            - team_id: the team_id
            - q_id_list: the question id list
        """
        qid_id_list_str = ' '.join(q_id_list)
        logger.info({
            "message": f"[Leaderboard] resend question {qid_id_list_str} of team {team_id}.",
            "trigger": "Leaderboard",
            "ENV": self.env
        })
        data = {"team_id": str(team_id), "qid": q_id_list}
        byted_data = json.dumps(data).encode("utf-8")
        try:
            future = self.publisher.publish(self.topic_path, byted_data, resend='y', team_id=str(team_id))
            logger.info({
                "message":f"[Leaderboard] pub msg success to {self.topic_path} with id: {future.result()}",
                "trigger": "Leaderboard",
                "ENV": self.env
            })
        except Exception as error:
            logger.critical({
                "message": f"[Leaderboard] pub msg failed with {error}",
                "trigger": "Leaderboard",
                "ENV": self.env
            })

    def get_q_num(self, conn):
        """
        Get questions from DB.

        Parameters:
            - conn: DB connection
        """
        sql = '''
                select qid from questions where send_date::timestamp::date = '%s'::date;
              ''' % (self.timestamp)
        q_id_list = pd.read_sql(sql, conn)['qid'].tolist()
        self.qid_str = "'" + "','".join(q_id_list) +"'"
        self.q_num = len(q_id_list)

    def get_verified_list(self, conn):
        """
        Get verified team id (status_code_infer==200) from DB.

        Parameters:
            - conn: DB connection
        """
        sql = '''
                select distinct team_id from verification where status_code_infer = 200;
              '''
        verified_list = pd.read_sql(sql, conn)['team_id']
        self.verified_list = [str(i) for i in verified_list]
        self.sub_name_list.extend(["team_{}_{}".format(i, self.env) for i in verified_list])

    def get_miss_team_list(self, conn):
        """
        Get team ids which had missed generated question from DB.

        Parameters:
            - conn: DB connection

        Returns:
            - the team id list
        """
        verified_str = "'" + "','".join(self.verified_list) +"'"
        sql = '''
                with
                  not_ok as
                    (select b.team_id, b.qid from
                      (select c.team_id, c.qid, count(*) from
                        (select distinct team_id, qid, retry from 
                          answers where post_time::timestamp::date >= '%s'::date and team_id in (%s) and qid in (%s) and status_code != 200) c group by c.team_id, c.qid) b
                            where b.count=3),
                  ok as
                    (select distinct team_id, qid from
                      answers where post_time::timestamp::date >= '%s'::date and team_id in (%s) and qid in (%s) and status_code in (200, 999))

                select b.team_id, count(*) from (select * from not_ok union select * from ok) b group by b.team_id;
              ''' % (self.timestamp, verified_str, self.qid_str,
                     self.timestamp, verified_str, self.qid_str)
        ans_num = pd.read_sql(sql, conn)
        ans_num = ans_num[ans_num["count"] != self.q_num]
        return ans_num["team_id"].tolist()

    def get_miss_id_list(self, conn, team_id):
        """
        Input team id and get question id list which had missed generated question from DB.

        Parameters:
            - conn: DB connection
            - team_id: the team id

        Returns:
            - miss_id_list: missing question id list
        """
        sql = '''
                with
                  not_ok as
                    (select b.team_id, b.qid from
                      (select c.team_id, c.qid, count(*) from
                        (select distinct team_id, qid, retry from 
                          answers where post_time::timestamp::date >= '%s'::date and team_id = '%s' and qid in (%s) and status_code != 200) c group by c.team_id, c.qid) b
                            where b.count=3),
                  ok as
                    (select distinct team_id, qid from
                      answers where post_time::timestamp::date >= '%s'::date and team_id = '%s' and qid in (%s) and status_code in (200, 999)),
                  total as
                    (select * from (select * from not_ok union all select * from ok) a),
                  qid as
                    (select qid from questions where send_date::timestamp::date = '%s'::date)

                select qid.qid from qid left join total on qid.qid = total.qid where total.qid is null;
              ''' % (self.timestamp, team_id, self.qid_str,
                     self.timestamp, team_id, self.qid_str,
                     self.timestamp)
        miss_id_list = pd.read_sql(sql, conn)['qid'].tolist()
        return miss_id_list

    def check(self):
        """
        Check if pubsub is empty and resend questions.

        Returns:
            - True : the pubsub is empty and it need not to resend questions.
            - False : the pubsub is not empty or it need to resend questions.
        """
        if not self.check_pubsub_empty():
            logger.info({
                "message": "[Leaderboard] Still leave some messages in pubsubs.",
                "trigger": "Leaderboard",
                "ENV": self.env
            })
            return False
        with get_conn() as conn:
            miss_team_list = self.get_miss_team_list(conn)
            if len(miss_team_list) > 0:
                logger.info({
                    "message": "[Leaderboard] Start to resend question.",
                    "trigger": "Leaderboard",
                    "ENV": self.env
                })
                for team_id in miss_team_list:
                    miss_id_list = self.get_miss_id_list(conn, team_id)
                    self.resend_question(team_id, miss_id_list)
                return False
        return True

if __name__ == '__main__':
    obj = Check_End_Signal(datetime.now())
    print(obj.check())