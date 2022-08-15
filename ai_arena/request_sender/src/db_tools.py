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
from psycopg2 import sql
from src.log_tool import logger
from contextlib import contextmanager
from psycopg2.extras import execute_values


class DBOperator():
    """
        DB connection
    """
    def __init__(self, log_msg):
        self._host = os.environ['DB_HOST']
        self._database = os.environ['DB_NAME']
        self._user = os.environ['DB_USER']
        self._password = os.environ['DB_PASS']
        self.log_msg = log_msg

    @contextmanager
    def get_conn(self):
        """
        Get connection from database.

        Returns:
            DB connection
        """
        conn = None
        try:
            conn = psycopg2.connect(
                host=self._host,
                database=self._database,
                user=self._user,
                password=self._password
            )
            yield conn
        except (Exception, psycopg2.DatabaseError) as error:
            self.log_msg.update({'message': f"[request_sender]  DB get connection error msg: {str(error)}"})
            logger.error(self.log_msg)
            raise RuntimeError(f"DB get connection Error: {str(error)}")
        finally:
            if conn:
                conn.close()


    def update_verification(self, status, verification_id):
        """
            Update verification table.

            parameters:
                status: status_code from request to competitors
                verificaton_id : verification_id from pulled message
        """
        sqlstring = sql.SQL("""
            update verification
            set status_code_infer = {status_code}
            where verification_id = {verification_id};
        """).format(
            status_code=sql.Literal(status),
            verification_id=sql.Literal(verification_id)
        )
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sqlstring)
                    conn.commit()
                self.log_msg.update({'message': f"[request_sender]  DB update_verification Finished!"})
                logger.info(self.log_msg)
            except Exception as error:
                self.log_msg.update({'message': f"[request_sender]  DB update_verification error msg: {str(error)}"})
                logger.error(self.log_msg)
                raise RuntimeError(f"DB update_verification Error: {str(error)}")


    def insert_answer(self, ans_list):
        """
            Insert competitors answer to answers table.

            parameters:
                ans_list: answers from competitors
        """
        sqlstring = sql.SQL(
            """
            insert into answers(
                qid, answer, team_id, post_time, get_time,
                status_code, retry, text, s_uuid, u_uuid, receive_time
            ) values
            ({qid}, {answer}, {team_id}, {post_time}, {get_time},
            {status_code}, {retry}, {text}, {s_uuid}, {u_uuid}, {receive_time})
            """
        ).format(
            qid = sql.Literal(ans_list[0]),
            answer = sql.Literal(ans_list[1]),
            team_id = sql.Literal(ans_list[2]),
            post_time = sql.Literal(ans_list[3]),
            get_time = sql.Literal(ans_list[4]),
            status_code = sql.Literal(ans_list[5]),
            retry = sql.Literal(ans_list[6]),
            text = sql.Literal(ans_list[7]),
            s_uuid = sql.Literal(ans_list[8]),
            u_uuid = sql.Literal(ans_list[9]),
            receive_time = sql.Literal(ans_list[10])
        )
        with self.get_conn() as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute(sqlstring)
                    conn.commit()
                self.log_msg.update({'message': f"[request_sender]  DB insert_answer finished!"})
                logger.info(self.log_msg)
            except Exception as error:
                self.log_msg.update({'message': f"[request_sender]  DB insert_answer error msg: {str(error)}"})
                logger.error(self.log_msg)
                raise RuntimeError(f"DB insert_answer Error: {str(error)}")
