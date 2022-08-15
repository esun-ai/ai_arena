#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
# @Author: Guan-Yu Su
# @Date: 2022/08
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
from google.cloud import logging


db_host = os.environ['DB_HOST']
db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASS']
FILE_NAME = os.environ['file_name']

logging_client = logging.Client()
logger = logging_client.logger(os.environ['LOGGER_NAME'])


def get_conn():
    conn = None
    try:
        logger.log_text("[Handler] Database connection starts.", severity='DEBUG')
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass
        )
    except (Exception, psycopg2.DatabaseError) as error:
        logger.log_text("DB connection Error: {} ".format(error), severity='ERROR')
        raise
    return conn


def read_sql():
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as curs:
                curs.execute(open(FILE_NAME, "r").read())
                conn.commit()
                logger.log_text("DB create schema and table successfully.", severity='INFO')
        conn.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.log_text("DB connection Error: {} ".format(error), severity='ERROR')
        raise

if __name__ == '__main__':
    read_sql()
