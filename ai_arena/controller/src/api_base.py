#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
# @Author: Tung-Chun Cheng
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
from datetime import date

from src.utils.logger import logger
from src.utils.db_tools import DBOperator
from src.utils.pubsub_tools import PubSubOperator
import src.utils.sql_generator as sql_generator

class APIBase():
    def __init__(self):
        self.env = os.environ['ENV']
        self.logger = logger
        self.contest_db = DBOperator()
        self.pubsub = PubSubOperator()

    def create_sub(self, team_id):
        """
            Create subscription for team
            Args:
                team_id(string): team id
            Return:
                None
            Raises:
                error: summary of runtime error message
        """
        try:
            self.pubsub.create_subscription(team_id)
        except Exception as error:
            raise error
    
    def get_sub(self):
        """
            Get subscriptions
            Args:
                team_id(string): team id
            Return:
                supscriptions(list)
            Raises:
                error: summary of runtime error message
        """
        try:
            subscriptions = self.pubsub.get_subscription()
            return subscriptions
        except Exception as error:
            raise error

    def delete_sub(self, team_id):
        """
            Delete subscription for team
            Args:
                team_id(string): team id
            Return:
                None
            Raises:
                error: summary of runtime error message
        """
        try:
            self.pubsub.delete_subscription(team_id)
        except Exception as error:
            raise error

    def verify_team_url(self, data):
        """
            Verify team's api service
            Args:
                team_id(string): team id
            Return:
                None
            Raises:
                error: summary of runtime error message
        """
        team_id = data["team_id"]
        team_url = data["team_url"]
        try:
            messages = self.pubsub.pull_message(team_id, team_url)
            self.pubsub.publish_verify_task(messages)
        except Exception as error:
            raise error

    def update_daily_task_status_table(self):
        """
            Update daily task status
            Args:
                team_id(string): team id
            Return:
                None
            Raises:
                error: summary of runtime error message
        """
        try:
            sqlstring = sql_generator.update_daily_task_status_sql()
            result = self.contest_db.execute_sql_with_return(sqlstring)
        except Exception as error:
            self.logger.error({
                    "message":f"[Controller] DB update status code Error: {error} ",
                    "ENV": self.env})
            raise error
        if not result:            
            self.logger.debug({'message':f'[Controller] Questions are already generated.',
                                'ENV':self.env})
            raise RuntimeError('questions already generated.')

        self.logger.info({
                "message": f"[Controller] Update daily task control table stauts success",
                'ENV': self.env})

    def pub_teams(self, competition_date):
        """
            Publish all verified team to generator
            Args:
                competition_date(string): date
            Return:
                seccess signal
            Raises:
                error: summary of runtime error message
        """
        if not competition_date:
            competition_date = date.today().isoformat()
        self.logger.debug({'message':f'[Controller] Start get registied teams.',
                        'date': competition_date,
                        'ENV':f'{self.env}'})
        try:
            self.logger.debug({'message':f'[Controller] Insert registied teams into generator_status.',
                            'date': competition_date,
                            'ENV':f'{self.env}'})
            sqlstring = sql_generator.insert_verified_teams_sql(competition_date)
            self.contest_db.execute_sql(sqlstring)
            self.logger.debug({'message':f'[Controller] Insert registied teams into generator_status succeeded.',
                            'date': competition_date,
                            'ENV':f'{self.env}'})
        except Exception as error:
            self.logger.error({'message':f'[Controller] Insert registied teams into generator_status error.',
                            'date': competition_date,
                            'error_message':str(error),
                            'ENV':f'{self.env}'})
            raise error

        try:
            sqlstring = sql_generator.update_status_sql(1,'',competition_date)
            teams = self.contest_db.execute_sql_with_return(sqlstring)
        except Exception as error:
            raise error

        self.logger.debug({'message':f'[Controller] Get all registied teams.',
                        'date': competition_date,
                        'ENV':f'{self.env}'})

        self.pubsub.publish_team_task(teams, 'Y', competition_date)
        return "all teams published"

    def pub_unit_team(self, team_id, competition_date):
        """
            Publish Specified verified team to generator
            Args:
                team_id(string): team id
                competition_date(string): date
            Return:
                seccess signal
            Raises:
                error: summary of runtime error message
        """
        if not competition_date:
            competition_date = date.today().isoformat()
        self.logger.debug({'message':f'[Controller] Check for registered team: team_{team_id}.',
                        'date': competition_date,
                        'ENV':f'{self.env}'})
        
        try:
            sqlstring = sql_generator.update_status_sql(1,team_id,competition_date)
            teams = self.contest_db.execute_sql_with_return(sqlstring)
        except Exception as error:
            raise error

        self.logger.debug({'message':f'[Controller] Registered team: team_{team_id}.',
                        'date': competition_date,
                        'ENV':f'{self.env}'})

        self.pubsub.publish_team_task(teams, '', competition_date)
        return f"team {team_id} published"

