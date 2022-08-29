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
import copy
import time
from concurrent.futures import TimeoutError

from src.utils.logger import logger
from src.utils.db_tools import DBOperator
from src.utils.pubsub_tools import PubSubOperator
import src.utils.sql_generator as sql_generator

class ControllerBase():
    def __init__(self):
        self.env = os.environ['ENV']
        self.logger = logger
        self.contest_db = DBOperator()
        self.pubsub = PubSubOperator()

    def start(self, message):
        """
        Start competition
        Parameters:
        Return:
        """

        self.logger.info({'message':'[Controller] Start competition'})

        sqlstring = sql_generator.get_verified_teams_sql()
        url_dict = self.contest_db.execute_sql_with_return(sqlstring)
        teams = copy.deepcopy(url_dict)
        
        try:
            sqlstring = sql_generator.get_verified_teams_sql()
            url_dict = self.contest_db.execute_sql_with_return(sqlstring)
            teams = copy.deepcopy(url_dict)
            teams.update({'message':"[Controller] Get today's teams",'total_teams':str(len(teams)),'ENV':f'{self.env}'})
            self.logger.info(teams)
        except Exception as error:
            return False, {'message':"[Controller] failed to get start teams",
                        'error_message':str(error),
                        'ENV':f'{self.env}'}
        try:
            self.pubsub.start_task(url_dict)
            return True, {'message':f'[Controller] all start task published',
                          'ENV':self.env}
        except TimeoutError:
            return True, {'message':f'[Controller] all start task published',
                          'ENV':self.env}
        except Exception as error:
            return False, {'message':"[Controller] failed to start competition",
                           'error_message':str(error),
                           'ENV':f'{self.env}'}

        
    def trigger_next(self, message):
        """
        Trigger next question for team
        Parameters:
            request body(json):
                team_id: string
        Return:
            status code
        """
        serial_id = int(time.time())
        data = message.attributes
        trigger_time = int(data['trigger_time']) if 'trigger_time' in data.keys() else 0
        self.logger.info({'message':f'[Controller] trigger next for team_{data["team_id"]}',
                        'team_id': data["team_id"],
                        'team_url': data['team_url'],
                        'qid': data["qid"],
                        'serial_id': serial_id,
                        'ENV':f'{self.env}'})
        try:
            pull_messages = self.pubsub.pull_message(data["qid"], data["team_id"], data['team_url'], trigger_time)
        except RuntimeError as error:
            return True, {'message': str(error),
                          'team_id': data["team_id"], 
                          'qid': data['qid'],
                          'serial_id': serial_id,
                          'ENV':f'{self.env}'}
        except Exception as error:
            return False, {'message':f'trigger next for team_{data["team_id"]}_{self.env}, qid: {data["qid"]} failed',
                            'team_id': data["team_id"], 
                            'qid': data['qid'],
                            'ENV':f'{self.env}',
                            'serial_id': serial_id,
                            'error_message': str(error)}

        if pull_messages:
            try:
                self.pubsub.publish_task(pull_messages)
            except Exception as error:
                return False, {'message':f'trigger next for team_{data["team_id"]}_{self.env} failed',
                            'team_id': data["team_id"], 
                            'ENV':f'{self.env}',
                            'old_qid':data['qid'],
                            'serial_id': serial_id, 
                            'error_message': str(error)}

        return True, {'message':f'trigger next for team_{data["team_id"]}_{self.env} succeeded',
                    'team_id':data["team_id"], 
                    'ENV':f'{self.env}',
                    'serial_id': serial_id,
                    'old_qid':data['qid']}

    def re_publish(self, team_id, qid, team_url):

        try:
            self.pubsub.re_trigger(team_id, qid, team_url, 0)
            self.logger.info({'message':'[Controller] republished message',
                            'team_id': f'{team_id}',
                            'qid': f'{qid}',
                            'ENV':f'{self.env}'})
        except Exception as error:
            self.logger.error({'message':f'[Controller] republish task failed',
                            'team_id': f'{team_id}',
                            'qid': f'{qid}',
                            'ENV':f'{self.env}',
                            'error':str(error)})