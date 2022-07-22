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
