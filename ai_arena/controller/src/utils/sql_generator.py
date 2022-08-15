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
from psycopg2 import sql

def update_daily_task_status_sql():
    """
        Generate update daily task status sql
        Change status from 0 to 1
        Args:
            None
        Return:
            sqlstring(str)
    """
    sqlstring = sql.SQL("""
                        UPDATE daily_task_status 
                           SET status= 1
                         WHERE status = 0
                     RETURNING status;
                        """)
    return sqlstring

def update_status_sql(status, team_id, date):
    """
        Generate update genetator status sql
        Change status from status to status - 1
        Args:
            status(int): current status for the team
            team_id(int): team's id
            date(str): competition date, e.g. '2022-06-27'
        Return:
            sqlstring(str)
    """
    team = f'team_id={team_id} AND' if team_id else ''
    sqlstring = sql.SQL("""
                        UPDATE generator_status 
                           SET insert_question_status = {STATUS} 
                         WHERE {TEAM} send_date::TIMESTAMP::DATE= '{DATE}'
                               AND insert_question_status={STATUS_NEXT} 
                     RETURNING team_id;""".format(STATUS = status,
                                                  TEAM = team,
                                                  DATE = date,
                                                  STATUS_NEXT = status-1
                                                )
                        )
    return sqlstring

def insert_verified_teams_sql(date):
    """
        Generate insert  generator status sql
        Insert into generator_status
        set team_id, timestamp, status
        Args:
            date(str): competition date, e.g. '2022-06-27'
        Return:
            sqlstring(str)
    """
    sqlstring = sql.SQL("""
                        INSERT INTO generator_status
                        SELECT DISTINCT(b.team_id) AS team_id,
                               '{DATE}'::TIMESTAMP,
                               '0'::INTEGER
                          FROM ( SELECT team_id,
                                        max(verification_time) AS ver_time
                                   FROM public.verification
                                  WHERE status_code_infer = 200
                                  GROUP BY team_id) AS a
                         INNER JOIN( SELECT team_id,
                                            verification_time,
                                            api_url
                                       FROM public.verification) AS b 
                            ON a.team_id = b.team_id 
                               AND a.ver_time = b.verification_time
                """.format(DATE=date))
    return sqlstring
