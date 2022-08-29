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
import psycopg2
from contextlib import contextmanager
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


class DBOperator(object):
    """
    Create DB connection with context manager
    """

    def __init__(self):
        self.env = env
        self._db = db
        self._host = db_host
        self._user = db_user
        self._password = db_pass

    @contextmanager
    def get_conn(self):
        """
        Get connection from database

        Returns:
            DB connection
        """
        conn = None
        try:
            logger.debug(f"[Generator] Getting DB connection at {env}")
            conn = psycopg2.connect(host=self._host,
                                    database=self._db,
                                    user=self._user,
                                    password=self._password)
            yield conn
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(
                f"[Generator] Create DB connection at {env} Error: {error}")
        finally:
            # Close the connection
            if conn:
                conn.close()

    def execute_sql_with_return(self, sql_string):
        """
        Execute sql string with return

        Args:
            conn: DB connection
            sql_string: SQL string to be executed
        """
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql_string)
                    result = cur.fetchall()
                    conn.commit()
                return result
            except Exception as error:
                logger.error(f"[Generator] Query DB at {env} Error: {error} ")
                raise RuntimeError(f"Query DB Error: {error}")

    def execute_sql(self, sql_string):
        """
        Execute sql string

        Args:
            sql_string: SQL string to be executed
        """
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql_string)
                    conn.commit()
            except Exception as error:
                logger.error(f"[Generator] Query DB at {env} Error: {error} ")
                raise RuntimeError(f"Query DB Error: {error}")
