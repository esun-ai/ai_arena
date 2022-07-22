import os
import psycopg2
from psycopg2 import sql

from src.utils.logger import logger

class DBOperator():
    def __init__(self):
        self.env = os.environ['ENV']
        self.logger = logger
        self.project_id = os.environ['PROJECT_ID']

    def get_conn(self):
        """
            Get connection with DB
            Args:
                None
            Return:
                None
            Raises:
                None
        """
        try:
            self.logger.debug(f"[Controller] Database connection at {self.env} starts.")
            conn = psycopg2.connect(host=os.environ['DB_HOST'],
                        database=os.environ['DB_NAME'],
                        user=os.environ['DB_USER'],
                        password=os.environ['DB_PASS'])

        except (Exception, psycopg2.DatabaseError) as error:
            self.logger.error(f"[Controller] DB connection at {self.env} Error: {error} ")

        self.logger.debug(f"[Controller] Database connected at {self.env} starts.")
        return conn
    
    def execute_sql_with_return(self, sqlstring):
        """
            Execute sql with return values
            Args:
                sqlstring(str): query sql string
            Return:
                result(list): query result
            Raises:
                RuntimeError: query db error
        """
        conn = self.get_conn()
        self.logger.info({'message': f'[Controller] Get DB connection: {conn} ',
                            'ENV': self.env})
        try:
            with conn.cursor() as cur:
                cur.execute(sqlstring)
                result = dict(cur.fetchall())
                self.logger.info({'message': f'[Controller] Get query result: {result} ',
                            'ENV': self.env})
            conn.commit()
            conn.close()
            return result
        except Exception as error:
            self.logger.error({'message': f'[Controller] Execute sql Error: {error} ',
                            'ENV': self.env})
            conn.close()
            raise RuntimeError(f"query DB Error: {error}")

    def execute_sql(self,sqlstring):
        """
            Execute sql with return values
            Args:
                sqlstring(str): query sql string
            Return:
                None
            Raises:
                RuntimeError: query db error
        """
        conn = self.get_conn()
        self.logger.info({'message': f'[Controller] Get DB connection: {conn} ',
                            'ENV': self.env})
        try:
            with conn.cursor() as cur:
                cur.execute(sqlstring)
            conn.commit()
            conn.close()
        except Exception as error:
            logger.error({'message': f'[Controller] Execute sql Error: {error}',
                            'ENV': self.env})
            conn.close()
            raise RuntimeError(f"query DB Error: {error}")

    
