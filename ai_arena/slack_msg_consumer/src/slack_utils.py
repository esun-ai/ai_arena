#!/usr/bin/env python
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
# -*- coding:utf-8 -*-
import os
import re
from datetime import datetime
import base64
from io import StringIO
import requests
import psycopg2
import numpy as np
import pandas as pd
import json
from urllib.parse import quote
from google.cloud import logging
from google.cloud import storage
from src.logger import logger

from src.format_utils import encrypt_email
from src.slack_bot_reply_msg import ReplyMessage

storage_client = storage.Client.from_service_account_json(
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
)
token = os.environ["SLACK_BOT_TOKEN"]
competition = os.environ["COMPETITION"]
slack_url = "https://slack.com/api/chat.postMessage"


def get_conn():
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ["DB_HOST"],
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            port=os.environ["DB_PORT"],
            keepalives=1,
        )
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error("DB connection Error: {} ".format(error))
    return conn


def slack_logger(log_level, message, slack_event_obj, **kwargs):
    """
    slack 相關的log都有必定會紀錄的固定欄位，所以使用統一 logger function 處理，避免欄位的值遺失
    """
    logger.log(
        getattr(logging, log_level),
        {message: message},
    )


def resend_otp(email_str, competition, input_text, channel):
    email = email_str.lower()
    encrypted_email = encrypt_email(email)
    reset_url = os.environ["RESET_URL"]

    headers = {"Content-Type": "application/json"}
    reset_info = {"email": email, "competition": competition}

    logger.debug(
        {
            "message": "[Forget_token] start getting token",
            "trigger": "Forget_token",
            "slack_channel": channel,
            "input": input_text,
            "origin_email": email_str,
            "extracted_email": email,
        }
    )
    if not competition.endswith("s"):
        try:
            r = requests.post(
                reset_url, headers=headers, data=json.dumps(reset_info), verify=False
            )
            if r.status_code != 200:
                logger.error(
                    {
                        "message": "[OTP internal failure] Error when send request to otp API with status_code: {}".format(
                            r.status_code
                        ),
                        "trigger": "Forget_token",
                        "slack_channel": channel,
                        "input": input_text,
                        "origin_email": email_str,
                        "extracted_email": email,
                        "post_payload": json.dumps(reset_info),
                        "response": str(r.status_code),
                    }
                )
                res = ReplyMessage.system_error
            else:
                if r.json()["status"] == 200:
                    res = "已寄出手機驗證碼至您於 T-Brain 報名留存的手機號碼"
                    logger.debug(
                        {
                            "message": "[Forget_token] OTP successfully sent.",
                            "trigger": "Forget_token",
                            "slack_channel": channel,
                            "input": input_text,
                            "origin_email": email_str,
                            "extracted_email": email,
                            "post_payload": json.dumps(reset_info),
                            "response": r.json(),
                        }
                    )
                elif r.json()["status"] == 404:
                    res = "找不到此 Email 資訊，請確認是否與您於 T-Brain 報名之 email 相同"
                    logger.debug(
                        {
                            "message": "[Forget_token] Email not found.",
                            "trigger": "Forget_token",
                            "slack_channel": channel,
                            "input": input_text,
                            "origin_email": email_str,
                            "extracted_email": email,
                            "post_payload": json.dumps(reset_info),
                            "response": r.json(),
                        }
                    )
                else:
                    logger.error(
                        {
                            "message": "[OTP internal failure] Error when send request to otp API.(status not valid)",
                            "trigger": "Forget_token",
                            "slack_channel": channel,
                            "input": input_text,
                            "origin_email": email_str,
                            "extracted_email": email,
                            "post_payload": json.dumps(reset_info),
                            "response": r.json(),
                        }
                    )
                    res = res = ReplyMessage.system_error
        except requests.exceptions.RequestException as e:
            send_to_slack(channel, input_text, res=ReplyMessage.SYSTEM_ERROR)
            logger.error(
                {
                    "message": "[OTP internal failure] Error when send request to otp API. (Exception caught!).",
                    "trigger": "Forget_token",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": email,
                    "post_payload": json.dumps(reset_info),
                    "Error": "{}".format(e),
                }
            )
    else:
        res = "這是dev 環境，不補發token"

    return res


def send_to_slack(channel, input_text, res):
    """
    send_to_slack _summary_

    Args:
        channel (_type_): _description_
        input_text (_type_): _description_
        res (_type_): _description_
    """
    myobj = {"token": token}
    myobj["as_user"] = True
    myobj["channel"] = channel
    myobj["text"] = res
    r = requests.post(slack_url, data=myobj)
    if r.status_code == 200:
        logger.info(
            {
                "message": "[E.SUN Reply Success!] to channel:{}, with input message:{} , reply message:{}".format(
                    channel, input_text, res
                ),
                "trigger": "Slack-bot-reply",
                "slack_channel": channel,
                "input": input_text,
                "reply": res,
                "posted_data": myobj,
            }
        )
    else:
        logger.error(
            {
                "message": "[E.SUN Reply Failed!] to channel:{}, with input message:{} , reply message:{}".format(
                    channel, input_text, res
                ),
                "trigger": "Slack-bot-reply",
                "slack_channel": channel,
                "input": input_text,
                "reply": res,
                "posted_data": myobj,
            },
            severity="CRITICAL",
        )


def is_in_process(cur):
    sql = "select status from daily_task_status"
    cur.execute(sql)
    status = cur.fetchone()[0]
    if status == 1:
        return True
    else:
        return False


def check_date_valid(date_str):
    DATE_REGEX = re.compile(r"([12]\d{3}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))")
    return DATE_REGEX.match(date_str)


def get_qids_of_date(conn, date_for_query):
    sql = """ select qid
            from questions 
            where competition = '%s' 
                and send_date = '%s'::date """ % (
        competition,
        str(date_for_query),
    )

    questions = pd.read_sql(sql, conn)
    qid_list = questions.qid.tolist()
    qid_list = [f"'{str(x)}'" for x in qid_list]
    qid_query_str = ",".join(qid_list)
    return qid_query_str


def team_log_exists(filename):
    bucket_name = os.environ["log_bucket_name"]
    bucket = storage_client.bucket(bucket_name)
    stats = storage.Blob(bucket=bucket, name=filename).exists(storage_client)
    return stats


def get_team_log_url(inference_log_filename):
    bucket_name = os.environ["log_bucket_name"]
    bucket = storage_client.bucket(bucket_name)
    inference_url = storage.Blob(bucket=bucket, name=inference_log_filename).public_url
    return inference_url


def get_log_of_team(conns, qid_query_str, team_id):
    inference_log = None
    inference_sql = """
            select a.s_uuid, a.post_time as request_start_time, a.receive_time as request_end_time, a.retry, b.status_desc as status, a.text as response_body 
            from answers a inner join status b on a.status_code=b.status_code
            where a.team_id = %s 
            and a.qid in (%s)
        """ % (
        str(team_id),
        qid_query_str,
    )
    inference_log = pd.read_sql(inference_sql, conns)
    return inference_log


def upload_blob(
    channel,
    input_text,
    team_id,
    date_for_query,
    bucket_name,
    df_name,
    source_df,
    destination_blob_name,
):
    f = StringIO()
    source_df.to_csv(f, index=False, encoding="utf-8")
    f.seek(0)

    bucket = storage_client.bucket(os.environ["log_bucket_name"])
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(f, content_type="text/csv")
    logger.info(
        {
            "message": "[Get_Log] File {} uploaded to gcp. ".format(df_name),
            "trigger": "Get_Log",
            "slack_channel": channel,
            "input": input_text,
            "team_id": str(team_id),
            "filename": df_name,
            "date_for_query": str(date_for_query),
        }
    )

    blob.make_public()
    logger.info(
        {
            "message": "[Get_Log] Blob {} is publicly accessible at {} ".format(
                blob.name, blob.public_url
            ),
            "trigger": "Get_Log",
            "slack_channel": channel,
            "input": input_text,
            "team_id": str(team_id),
            "filename": df_name,
            "blob_name": blob.name,
            "public_url": blob.public_url,
            "date_for_query": str(date_for_query),
        }
    )
    return blob.public_url


def make_log_public(
    channel, input_text, team_id, date_for_query, inference_log, inference_log_filename
):
    inference_url = upload_blob(
        channel,
        input_text,
        team_id,
        date_for_query,
        os.environ["log_bucket_name"],
        "inference_log",
        inference_log,
        inference_log_filename,
    )
    return inference_url


def send_log_to_slack(channel, input_text, team_id, date_for_query, inference_url):
    myobj2 = {
        "token": token,
        "channel": channel,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Your inference log of "
                    + str(date_for_query)
                    + " is <"
                    + inference_url
                    + "|HERE>",
                },
            },
        ],
    }
    headers = {"Content-type": "application/json", "Authorization": "Bearer " + token}
    r = requests.post(slack_url, data=json.dumps(myobj2), headers=headers)
    if r.status_code == 200:
        logger.info(
            {
                "message": "[E.SUN Reply Success!] to channel:{}, with input message:{} ".format(
                    channel, input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "team_id": str(team_id),
                "inference_url": inference_url,
                "date_for_query": str(date_for_query),
                "posted_data": json.dumps(myobj2),
            }
        )
    else:
        logger.error(
            {
                "message": "[E.SUN Reply Failed!] to channel:{}, with input message:{} ".format(
                    channel, input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "team_id": str(team_id),
                "inference_url": inference_url,
                "date_for_query": str(date_for_query),
                "posted_data": json.dumps(myobj2),
            }
        )


def get_latest_date(cur):
    date_for_query = None

    sql = """
            select max(post_time)::timestamp::date
            from answers;
        """
    cur.execute(sql)
    date_for_query = cur.fetchone()[0]
    if date_for_query:
        date_for_query = str(date_for_query)
        date_for_query = datetime.strptime(date_for_query, "%Y-%m-%d")
    return date_for_query
