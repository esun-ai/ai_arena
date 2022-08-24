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

import pandas as pd
import psycopg2
import os
import pytz
from datetime import datetime
from src.logger import logger

tw = pytz.timezone('Asia/Taipei')
utc = pytz.utc

def get_conn():
    """
    Get DB connection.

    Return: DB connection
    """
    conn = None
    try:
        logger.debug("Database connection starts.")
        conn = psycopg2.connect(host=os.environ['DB_HOST'],
                    database=os.environ['DB_NAME'],
                    user=os.environ['DB_USER'],
                    password=os.environ['DB_PASS'])
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error("DB connection Error: {} ".format(error))
    return conn

def is_in_process():
    """
    Check the task status.

    Return:
      - True: the task is in process
      - False: the task is not in process
    """
    with get_conn() as conns:
        sql = 'select status from daily_task_status'
        df = pd.read_sql(sql, conns)
        if df.loc[0, 'status'] == 1:
            return True
        else:
            return False

def get_now_timestamp():
    """
    Get current timestamp.

    Return: current timestamp
    """
    dt = datetime.now()
    utc_dt = utc.localize(dt)
    now_timestamp = utc_dt.astimezone(tw)
    return now_timestamp
    