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
import os
import json
import pandas as pd
import requests
import hashlib
from datetime import datetime
from google.cloud import pubsub_v1
from src.slack_bot_reply_msg import ReplyMessage
from src.slack_utils import get_conn
from src.format_utils import extract_email, extract_token, extract_url, encrypt_email
from src.format_utils import email_format_match, token_format_match, check_url_valid
from src.format_utils import get_now_timestamp
from src.slack_utils import send_to_slack, resend_otp
from src.slack_utils import (
    get_latest_date,
    send_log_to_slack,
    team_log_exists,
    get_team_log_url,
)
from src.slack_utils import (
    get_qids_of_date,
    get_log_of_team,
    make_log_public,
    check_date_valid,
)
from src.slack_utils import is_in_process
from src.logger import logger
from src.slack_utils import slack_logger

# general handler use
conn = get_conn()
competition = os.environ["COMPETITION"]
# verification handler use
create_sub_url = os.environ["CREATE_SUB_URL"]
verify_url = os.environ["VERIFY_URL"]
project_id = os.environ["PROJECT_ID"]
topic_id = os.environ["TOPIC_ID"]
env = os.environ["ENV"]
# get log  handler use
log_start_date = os.environ["LOG_START_DATE"]

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)


def forget_token_handler(channel, text_list):
    """
    參賽者要求重發token
    Args:
        channel:str, slack channel id
        func:list, 合格的func應為['forget_token', '參賽者email']
    Returns:
        res:回傳給參賽者的文字

    """
    res = ""
    exec_result = 3
    func = text_list
    input_text = str(text_list)
    if len(func) != 2:
        res = "請輸入正確的 forget_token 格式：forget_token [email_of_team_leader]"
        exec_result = 381
        logger.debug(
            {
                "message": "[Forget_token] Functional call wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Forget_token",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not email_format_match(func[1]):
        res = ReplyMessage.EMAIL_FORMAT_ERROR
        exec_result = 382
        logger.debug(
            {
                "message": "[Forget_token] Functional Email wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Forget_token",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
                "origin_email": func[1],
                "extracted_email": extract_email(func[1]).lower(),
            }
        )
    else:
        email_str = extract_email(func[1]).lower()

        res = resend_otp(email_str, competition, input_text, channel)
    send_to_slack(channel, input_text, res)
    return exec_result


def register_handler(channel, text_list):
    """
    合格text_list = ['register','隊長email','驗證碼']

    會call controller 去登記topic=lake 的suscribtion
    如果當天是比賽天
    """
    res = ""
    func = text_list
    input_text = str(text_list)
    if len(func) != 3:
        res = "請輸入正確的 register 格式：register [email_of_team_leader] [phone_token_of_team_leader]"
        logger.debug(
            {
                "message": "[Register] Functional call wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Register",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not email_format_match(func[1]):
        res = ReplyMessage.EMAIL_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Register] Functional Email wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Register",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not token_format_match(func[2]):
        res = ReplyMessage.TOKEN_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Register] OTP token wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Register",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    else:
        extracted_email = extract_email(func[1]).lower()
        email = encrypt_email(extracted_email)
        token = extract_token(func[2])
        logger.debug(
            {
                "message": "[Register] Register Starts, extract neccessary infos from input : {}".format(
                    input_text
                ),
                "trigger": "Register",
                "slack_channel": channel,
                "input": input_text,
                "extracted_email": extracted_email,
                "encrypted_email": email,
                "token": token,
            }
        )
        conn = get_conn()
        with conn.cursor() as cur:
            sql = """ select exists(select 1 from public.users where email=%s and competition=%s and code=%s)"""
            cur.execute(sql, (email, str(competition), token))

            users_exists_result = cur.fetchone()
            if users_exists_result:
                users_exists = users_exists_result[0]

            leader_sql = """ select team_name, team_leader_ind from tbrain_info where competition = %s and email = %s """
            cur.execute(leader_sql, (competition, email))
            team_leader_result = cur.fetchone()
            logger.debug(
                {
                    "message": f"team_leader_result: {team_leader_result}",
                    "trigger": "Register",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                }
            )
            if users_exists and team_leader_result:
                sql = """select exists(select 1 from public.register where email=%s and competition=%s)"""
                cur.execute(sql, (email, str(competition)))
                if cur.fetchone()[0]:
                    res = "您已經註冊過，可以使用 verification 指令開始驗證"
                    logger.debug(
                        {
                            "message": "[Register] Team already registered.",
                            "trigger": "Register",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                        }
                    )
                else:
                    if team_leader_result[1] == False:
                        res = "請使用隊長的 email 與手機驗證碼註冊正式賽"
                        logger.debug(
                            {
                                "message": "[Register] Not using leaders email and token.",
                                "trigger": "Register",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                            }
                        )
                    else:
                        insert_sql = """insert into public.register (competition, email, code, team_name, status_code)
                                            values(%s,%s,%s,%s,%s) returning team_id"""
                        cur.execute(
                            insert_sql,
                            (competition, email, token, team_leader_result[0], 1),
                        )
                        team_id = cur.fetchone()[0]
                        url = create_sub_url
                        data = {"team_id": team_id}
                        response = requests.post(url, json=data)
                        if response.status_code == 200 or response.status_code == 409:
                            res = "註冊成功!"
                            logger.debug(
                                {
                                    "message": "[Register] Successfully registered.",
                                    "trigger": "Register",
                                    "slack_channel": channel,
                                    "input": input_text,
                                    "extracted_email": extracted_email,
                                    "encrypted_email": email,
                                    "token": token,
                                }
                            )
                            conn.commit()
                        else:

                            logger.info(
                                {
                                    "message": f"pubsub suscribe not 200 with code: {response.status_code}",
                                    "trigger": "Register",
                                    "slack_channel": channel,
                                    "input": input_text,
                                    "extracted_email": extracted_email,
                                    "encrypted_email": email,
                                    "token": token,
                                }
                            )
                            res = ReplyMessage.SYSTEM_ERROR
                            conn.rollback()
            else:
                res = "經查詢，您非本次競賽參賽者，請確認已在 T-Brain 報名比賽或確認使用的 email 及手機驗證碼與 T-Brain 報名時相同，若忘記手機驗證碼，可輸入 forget_token [your_email] 重新取得"
                logger.debug(
                    {
                        "message": "[Register] Email not found in DB users.",
                        "trigger": "Register",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                    }
                )
            conn.commit()
    conn.close()
    send_to_slack(channel, input_text, res)
    return "register handler success"


def verification_handler(channel, text_list):
    """參賽者驗證API格式是否正確
    :param：
        channel:str, slack channel id
        func:list, 合格的func應為['verification', '參賽者email', 'OTP token', 'api_url']
    :return:
        res:回傳給參賽者是否驗證成功的文字
    """
    res = ""
    verification_time = get_now_timestamp()
    func = text_list
    input_text = str(text_list)
    conn = get_conn()
    with conn.cursor() as cur:
        if is_in_process(cur):
            res = "比賽進行中，verification 功能關閉"
            send_to_slack(channel, input_text, res)
            return " verification handler success"

    if len(func) != 4:
        res = "請輸入正確的 verification 格式：\nverification [email_of_team_leader] [phone_token_of_team_leader] http://[external_IP_of_your_VM]:[port_of_your_API]"
        logger.debug(
            {
                "message": "[Verification] Functional call wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Verification",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
                "verification_time": str(verification_time),
            }
        )
    elif not email_format_match(func[1]):
        res = ReplyMessage.EMAIL_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Verification] Functional Email wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Verification",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
                "origin_email": func[1],
                "extracted_email": extract_email(func[1]).lower(),
                "verification_time": str(verification_time),
            }
        )
    elif not token_format_match(func[2]):
        res = ReplyMessage.TOKEN_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Verification] OTP token wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Verification",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
                "verification_time": str(verification_time),
            }
        )
    else:
        extracted_email = extract_email(func[1]).lower()
        email = encrypt_email(extracted_email)
        token = extract_token(func[2])
        api_url = extract_url(func[3])

        logger.debug(
            {
                "message": "[Verification] Verification Starts, extract neccessary infos from input : {}".format(
                    input_text
                ),
                "trigger": "Verification",
                "slack_channel": channel,
                "input": input_text,
                "extracted_email": extracted_email,
                "encrypted_email": email,
                "token": token,
                "extracted_api_url": api_url,
                "verification_time": str(verification_time),
            }
        )

        if not check_url_valid(api_url):
            logger.debug(
                {
                    "message": "[Verification] Wrong API URL format from input: {}".format(
                        input_text
                    ),
                    "trigger": "Verification",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                    "extracted_api_url": api_url,
                    "verification_time": str(verification_time),
                }
            )
            res = ReplyMessage.API_FROMAT_ERROR
            send_to_slack(channel, input_text, res)
            return "verification handler detect wrong api url format"

        # 防止 sql injection #
        api_url_lower = api_url.lower()
        if (
            ";" in api_url_lower
            or "select" in api_url_lower
            or "drop" in api_url_lower
            or "insert" in api_url_lower
            or "update" in api_url_lower
            or "truncate" in api_url_lower
        ):
            logger.warning(
                {
                    "message": "[Verification] Detect SQL injection from input: {}".format(
                        input_text
                    ),
                    "trigger": "Verification",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                    "extracted_api_url": api_url,
                    "verification_time": str(verification_time),
                }
            )

            res = ReplyMessage.API_URL_FROMAT_ERROR
            send_to_slack(channel, input_text, res)
            return "verification handler detect sql injetion"

        with conn.cursor() as cur:
            sql = "select team_id, code from public.register where email=%s and competition=%s"
            logger.debug(
                {
                    "message": "[Verification] Try to get team_id from register db.",
                    "trigger": "Verification",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                    "extracted_api_url": api_url,
                    "verification_time": str(verification_time),
                }
            )
            cur.execute(sql, (email, competition))
            result = cur.fetchone()
            if result:
                logger.debug(
                    {
                        "message": "[Verification] Successfully get register info from register db.",
                        "trigger": "Verification",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                        "extracted_api_url": api_url,
                        "register_info": str(result),
                        "verification_time": str(verification_time),
                    }
                )

                if token == result[1]:
                    team_id = result[0]
                    logger.debug(
                        {
                            "message": "[Verification] OTP check success! Successfully get team_id from register db. Start verification.",
                            "trigger": "Verification",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "extracted_api_url": api_url,
                            "team_id": str(team_id),
                            "verification_time": str(verification_time),
                        }
                    )

                    sql = """select exists
                            (select 1 from public.verification 
                            where api_url=%s
                            and team_id!=%s 
                            and status_code_infer=200)"""
                    cur.execute(sql, (api_url, str(team_id)))
                    if cur.fetchone()[0]:
                        res = "驗證失敗，請再次檢查您所輸入的 email、手機驗證碼或 API URL 是否正確，若仍有疑問請寄信至 intelligent-finance@esunbank.com.tw 或於活動 Slack 以私訊方式與主辦單位聯繫，並提供您於 T-Brain 註冊的 email 與 API URL，謝謝"
                        logger.warning(
                            {
                                "message": "[Verification] Detect trying to use an API url that was used by other team.",
                                "trigger": "Verification",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "extracted_api_url": api_url,
                                "team_id": str(team_id),
                                "verification_time": str(verification_time),
                            }
                        )
                    else:
                        sha = hashlib.sha256()
                        sha.update(
                            (str(team_id) + str(verification_time)).encode("utf-8")
                        )
                        verification_id = sha.hexdigest()

                        logger.info(
                            {
                                "message": "[Verification] Generate verification_id.",
                                "trigger": "Verification",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "extracted_api_url": api_url,
                                "team_id": str(team_id),
                                "esun_uuid": verification_id,
                                "verification_time": str(verification_time),
                            }
                        )

                        insert_sql = "insert into public.verification (verification_id, team_id, api_url, verification_time) values (%s, %s, %s, %s)"

                        logger.info(
                            {
                                "message": "[Verification] Insert default info to public.verification DB.",
                                "trigger": "Verification",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "extracted_api_url": api_url,
                                "team_id": str(team_id),
                                "esun_uuid": verification_id,
                                "verification_time": str(verification_time),
                            }
                        )

                        cur.execute(
                            insert_sql,
                            (
                                verification_id,
                                str(team_id),
                                api_url,
                                str(verification_time),
                            ),
                        )
                        conn.commit()
                        data = {
                            "esun_uuid": verification_id,
                            "question": "verification question",
                            "retry": "2",
                        }
                        byted_data = json.dumps(data).encode("utf-8")
                        try:
                            future = publisher.publish(
                                topic_path,
                                byted_data,
                                team_id=str(team_id),
                                team="team_" + str(team_id) + "_" + env,
                                team_url=api_url,
                                slack_channel=channel,
                                is_verification="True",
                                esun_uuid=verification_id,
                                qid="0000",
                                verification_id=verification_id,
                            )

                            logger.info(
                                {
                                    "message": f"[Slack] pub msg success to {topic_path} with id: {future.result()}",
                                    "esun_uuid": verification_id,
                                }
                            )
                            data = {"team_id": team_id, "team_url": api_url}
                            response = requests.post(verify_url, json=data)
                            logger.info(
                                {
                                    "message": f"[Slack] trigger verify_url returning status code {response.status_code} and text: {response.text}",
                                    "post_data": str(data),
                                    "esun_uuid": str(verification_id),
                                }
                            )

                            res = ReplyMessage.get_verification_success_res()
                        except Exception as e:
                            logger.error({"message": f"pub msg failed with {e}"})
                            res = ReplyMessage.SYSTEM_ERROR
                else:
                    res = ReplyMessage.TOKEN_ERROR
                    logger.debug(
                        {
                            "message": "[Verification] OTP incorrect! Failed to get team_id. Reply to slack.",
                            "trigger": "Verification",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "extracted_api_url": api_url,
                            "verification_time": str(verification_time),
                        }
                    )
            else:
                res = "驗證失敗：請先註冊，或檢查是否輸入錯誤的 email"
                logger.debug(
                    {
                        "message": "[Verification] Team not registered, cannot get team_id.",
                        "trigger": "Verification",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                        "extracted_api_url": api_url,
                        "verification_time": str(verification_time),
                    }
                )
            conn.commit()
    conn.close()
    send_to_slack(channel, input_text, res)
    logger.info(
        {
            "message": "[Verification] Finish Verification process.",
            "trigger": "Verification",
            "slack_channel": channel,
            "input": input_text,
            "verification_time": str(verification_time),
        }
    )
    return "verification handler success"


def get_status_handler(channel, text_list):
    func = text_list
    input_text = str(text_list)
    if len(func) != 3:
        res = "請輸入正確的 get_status 格式：get_status [email_of_team_leader] [phone_token_of_team_leader]"
        logger.debug(
            {
                "message": "[Get_Status] Functional call wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Status",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not email_format_match(func[1]):
        res = ReplyMessage.EMAIL_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Get_Status] Functional Email wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Status",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not token_format_match(func[2]):
        res = ReplyMessage.TOKEN_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Get_Status] OTP token wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Status",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    else:
        extracted_email = extract_email(func[1]).lower()
        email = encrypt_email(extracted_email)
        token = extract_token(func[2])

        # extracted_email 不等於

        logger.debug(
            {
                "message": "[Get_Status] Get_Status Starts, extract neccessary infos from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Status",
                "slack_channel": channel,
                "input": input_text,
                "extracted_email": extracted_email,
                "encrypted_email": email,
                "token": token,
            }
        )
        conn = get_conn()
        with conn.cursor() as cur:
            sql = (
                "select team_id, code from public.register where email='%s' and competition='%s'"
                % (email, competition)
            )
            logger.debug(
                {
                    "message": "[Get_Status] Try to get team_id from register db.",
                    "trigger": "Get_Status",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                }
            )

            team_info = pd.read_sql(sql, conn)

            if not team_info.empty:
                logger.debug(
                    {
                        "message": "[Get_Status] Successfully get team register info from register db.",
                        "trigger": "Get_Status",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                        "team_info": team_info.to_json(orient="records"),
                    }
                )

                if token == team_info.loc[0, "code"]:
                    logger.debug(
                        {
                            "message": "[Get_Status] Successfully check OTP token correct, and get team_id. Start to get status.",
                            "trigger": "Get_Status",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "team_id": str(team_info.loc[0, "team_id"]),
                        }
                    )

                    sql = """select * from public.verification
                                where team_id=%s
                                and verification_time=(
                                    select max(verification_time) from public.verification where team_id=%s)
                            """ % (
                        str(team_info.loc[0, "team_id"]),
                        str(team_info.loc[0, "team_id"]),
                    )
                    df = pd.read_sql(sql, conn)
                    if not df.empty:
                        logger.debug(
                            {
                                "message": "[Get_Status] Successfully get verification records from verification db.",
                                "trigger": "Get_Status",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "team_id": str(team_info.loc[0, "team_id"]),
                                "verification_records": df.to_json(orient="records"),
                            }
                        )

                        sql = """select * from public.status"""
                        status_desc = pd.read_sql(sql, conn)
                        if df.loc[0, "status_code_infer"] == 200:
                            res = (
                                "最近一次驗證時間為："
                                + str(df.loc[0, "verification_time"])
                                + ", 驗證api url為："
                                + str(df.loc[0, "api_url"])
                                + ", 驗證狀態為：成功"
                            )
                        elif (
                            pd.isna(df.loc[0, "status_code_infer"]) == False
                            and df.loc[0, "status_code_infer"] != 200
                        ):
                            if df.loc[0, "status_code_infer"] == 999:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, api 回傳格式錯誤, 請再做檢查"
                                )
                            elif df.loc[0, "status_code_infer"] == 900:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, 您的伺服器無回應, 請確認是否開啟"
                                )
                            elif df.loc[0, "status_code_infer"] == 901:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, 從您的api提取回應失敗, 請確認服務已啟用"
                                )
                            elif df.loc[0, "status_code_infer"] == 902:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, 連線失敗, 請確認您的網路狀態是否正常"
                                )
                            elif df.loc[0, "status_code_infer"] == 903:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, 連線逾時, 請確認是否在時間內回傳"
                                )
                            elif df.loc[0, "status_code_infer"] == 904:
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, 您的api url 格式錯誤, 請檢查後重新驗證"
                                )
                            else:
                                df = pd.merge(
                                    df,
                                    status_desc.rename(
                                        columns={
                                            "status_code": "status_code_infer",
                                            "status_desc": "status_infer_desc",
                                        }
                                    ),
                                    how="left",
                                    on=["status_code_infer"],
                                )
                                res = (
                                    "最近一次驗證時間為："
                                    + str(df.loc[0, "verification_time"])
                                    + ", 驗證api url為："
                                    + str(df.loc[0, "api_url"])
                                    + ", 驗證狀態為：Inference 階段失敗, "
                                    + str(df.loc[0, "status_code_infer"])
                                    + " "
                                    + str(df.loc[0, "status_infer_desc"])
                                )
                        else:
                            res = ReplyMessage.SYSTEM_ERROR
                            logger.error(
                                {
                                    "message": "[Get_Status] The status of the verification records is in wrong format. Please check verification db.",
                                    "trigger": "Get_Status",
                                    "slack_channel": channel,
                                    "input": input_text,
                                    "extracted_email": extracted_email,
                                    "encrypted_email": email,
                                    "token": token,
                                    "team_id": str(team_info.loc[0, "team_id"]),
                                    "verification_records": df.to_json(
                                        orient="records"
                                    ),
                                }
                            )
                    else:
                        res = "您尚未驗證過，請用 verification 指令進行驗證"
                        logger.debug(
                            {
                                "message": "[Get_Status] Did not find any verification log for the team.",
                                "trigger": "Get_Status",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "team_id": str(team_info.loc[0, "team_id"]),
                            }
                        )
                else:
                    logger.debug(
                        {
                            "message": "[Get_Status] OTP token incorrect. Reply to slack.",
                            "trigger": "Get_Status",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "team_info": team_info.to_json(orient="records"),
                        }
                    )
                    res = "您的手機驗證碼輸入錯誤，請再次檢查資訊是否輸入正確！"
            else:
                res = "您尚未使用 register 指令註冊過正式賽，或是您的 email 輸入錯誤，請再次檢查資訊是否輸入正確！"
                logger.debug(
                    {
                        "message": "[Get_Status] Did not find any register log for the team.",
                        "trigger": "Get_Status",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                    }
                )
            conn.commit()
    conn.close()
    send_to_slack(channel, input_text, res)
    logger.info(
        {
            "message": "[Get_Status] Finish get status process.",
            "trigger": "Get_Status",
            "slack_channel": channel,
            "input": input_text,
        }
    )
    return "get_status handler success"


def get_log_handler(channel, text_list):
    log_start_date = os.environ["LOG_START_DATE"]
    res = ""
    logger.info(
        {
            "message": "[Get_Log] Handler start and get valid payload.",
            "trigger": "Get_Log",
        }
    )

    func = text_list
    input_text = str(text_list)
    channel = channel

    conn = get_conn()
    with conn.cursor() as cur:
        if is_in_process(cur):
            res = ReplyMessage.GET_LOG_CLOSED
            send_to_slack(channel, input_text, res)
            return "get_log handler success"

    if len(func) != 3 and len(func) != 4:
        res = ReplyMessage.GET_LOG_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Get_Log] Functional call wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not email_format_match(func[1]):
        res = ReplyMessage.EMAIL_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Get_Log] Functional Email wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif not token_format_match(func[2]):
        res = ReplyMessage.TOKEN_FORMAT_ERROR
        logger.debug(
            {
                "message": "[Get_Log] OTP token wrong format from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "func": func,
            }
        )
    elif datetime.now() < datetime.strptime(log_start_date, "%Y-%m-%d"):
        res = f"此功能尚未開放，待測試賽後才開放使用，開放此功能日期為:{log_start_date}"
    else:
        if len(func) == 3:  # 無指定時間，給 healthcheck_log 中最新時間的 log
            logger.debug(
                {
                    "message": "[Get_Log] No assign get_log date, try to get latest date from questions db",
                    "trigger": "Get_Log",
                    "slack_channel": channel,
                    "input": input_text,
                    "func": func,
                }
            )

            with conn.cursor() as cur:
                date_for_query = get_latest_date(cur)

            if not date_for_query:
                logger.debug(
                    {
                        "message": "[Get_Log] Date out of valid range. Its the first day of competition",
                        "trigger": "Get_Log",
                        "slack_channel": channel,
                        "input": input_text,
                        "func": func,
                        "date_for_query": str(date_for_query),
                    }
                )
                res = "尚未有競賽的 log 可供查詢，您可於測試賽開始後的第二天，開放查詢前一天以前的 log"
                send_to_slack(channel, input_text, res)
                return "get_log handler success"
            else:
                logger.debug(
                    {
                        "message": "[Get_Log] Succesfully get the latest date for query.",
                        "trigger": "Get_Log",
                        "slack_channel": channel,
                        "input": input_text,
                        "func": func,
                        "date_for_query": str(date_for_query),
                    }
                )

        else:  # 指定 log 時間
            date_str = func[3]
            if not check_date_valid(date_str):
                res = ReplyMessage.DATE_FORMAT_ERROR
                logger.debug(
                    {
                        "message": "[Get_Log] Date wrong format from input : {}".format(
                            input_text
                        ),
                        "trigger": "Get_Log",
                        "slack_channel": channel,
                        "input": input_text,
                        "func": func,
                    }
                )
                send_to_slack(channel, input_text, res)
                return "get_log handler success"
            else:
                date_for_query = datetime.strptime(date_str, "%Y-%m-%d")
                with conn.cursor() as cur:
                    latest_date = get_latest_date(cur)

                if date_for_query > latest_date:
                    res = "欲查詢 log 的日期不在合法範圍內，只能查詢 {} 以前的 log".format(
                        latest_date.strftime("%Y-%m-%d")
                    )
                    logger.debug(
                        {
                            "message": "[Get_Log] Date out of valid range from input : {}".format(
                                input_text
                            ),
                            "trigger": "Get_Log",
                            "slack_channel": channel,
                            "input": input_text,
                            "func": func,
                            "date_for_query": str(date_for_query),
                            "latest_date": str(latest_date),
                        }
                    )
                    send_to_slack(channel, input_text, res)
                    return "get_log handler success"

        extracted_email = extract_email(func[1]).lower()
        email = encrypt_email(extracted_email)
        token = extract_token(func[2])
        logger.debug(
            {
                "message": "[Get_Log] Get_Log Starts, extract neccessary infos from input : {}".format(
                    input_text
                ),
                "trigger": "Get_Log",
                "slack_channel": channel,
                "input": input_text,
                "extracted_email": extracted_email,
                "encrypted_email": email,
                "token": token,
                "date_for_query": str(date_for_query),
            }
        )

        with conn.cursor() as cur:
            sql = (
                "select team_id, code from public.register where email='%s' and competition='%s'"
                % (email, competition)
            )
            logger.debug(
                {
                    "message": "[Get_Log] Try to get team_id from register db.",
                    "trigger": "Get_Log",
                    "slack_channel": channel,
                    "input": input_text,
                    "extracted_email": extracted_email,
                    "encrypted_email": email,
                    "token": token,
                    "date_for_query": str(date_for_query),
                }
            )
            team_info = pd.read_sql(sql, conn)
            if not team_info.empty:
                logger.debug(
                    {
                        "message": "[Get_Log] Successfully get team register info from register db.",
                        "trigger": "Get_Log",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                        "date_for_query": str(date_for_query),
                        "team_info": team_info.to_json(orient="records"),
                    }
                )

                if token == team_info.loc[0, "code"]:
                    logger.debug(
                        {
                            "message": "[Get_Log] Successfully check OTP token correct, and get team_id. Start to get log.",
                            "trigger": "Get_Log",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "date_for_query": str(date_for_query),
                            "team_id": str(team_info.loc[0, "team_id"]),
                        }
                    )

                    team_id = team_info.loc[0, "team_id"]
                    encrypt_team_id = encrypt_teamid(str(team_id))
                    inference_log_filename = (
                        "inference-log-of-team-"
                        + encrypt_team_id
                        + "-"
                        + str(date_for_query)
                        + ".csv"
                    )
                    if team_log_exists(inference_log_filename):
                        logger.debug(
                            {
                                "message": "[Get_Log]  Log file already exists! Get public url from gcp bucket.",
                                "trigger": "Get_Log",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "date_for_query": str(date_for_query),
                                "inference_filename": inference_log_filename,
                                "team_id": str(team_id),
                            }
                        )

                        inference_url = get_team_log_url(inference_log_filename)
                        logger.debug(
                            {
                                "message": "[Get_Log]  Finish get log url from gcp bucket.",
                                "trigger": "Get_Log",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "date_for_query": str(date_for_query),
                                "inference_filename": inference_log_filename,
                                "inference_url": inference_url,
                                "team_id": str(team_id),
                            }
                        )
                    else:
                        logger.debug(
                            {
                                "message": "[Get_Log]  Log file doesn't exists! Start getting log from db and upload to gcp bucket.",
                                "trigger": "Get_Log",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "date_for_query": str(date_for_query),
                                "inference_filename": inference_log_filename,
                                "team_id": str(team_id),
                            }
                        )

                        qid_query_str = get_qids_of_date(conn, date_for_query)

                        if not qid_query_str:  # 所查詢的日期並無發送題目紀錄
                            logger.debug(
                                {
                                    "message": "[Get_Log] There is no qids of the query date. Reply to slack",
                                    "trigger": "Get_Log",
                                    "slack_channel": channel,
                                    "input": input_text,
                                    "extracted_email": extracted_email,
                                    "encrypted_email": email,
                                    "token": token,
                                    "date_for_query": str(date_for_query),
                                    "qid_list": qid_query_str,
                                    "team_id": str(team_id),
                                }
                            )
                            res = ReplyMessage.get_no_qid_res(
                                date_for_query.strftime("%Y-%m-%d")
                            )
                            send_to_slack(channel, input_text, res)
                            return "get_log handler success"

                        logger.debug(
                            {
                                "message": "[Get_Log] Get qid list of the query date.",
                                "trigger": "Get_Log",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "date_for_query": str(date_for_query),
                                "team_id": str(team_id),
                            }
                        )

                        inference_log = get_log_of_team(conn, qid_query_str, team_id)
                        logger.debug(
                            {
                                "message": "[Get_Log] Get question log of the team.",
                                "trigger": "Get_Log",
                                "slack_channel": channel,
                                "input": input_text,
                                "extracted_email": extracted_email,
                                "encrypted_email": email,
                                "token": token,
                                "date_for_query": str(date_for_query),
                                "inference_log_cols": str(inference_log),
                                "team_id": str(team_id),
                            }
                        )

                        if inference_log is None:  # 尚未驗證過，所以根本沒發題給參賽者
                            logger.debug(
                                {
                                    "message": "[Get_Log] There is no log of the team. Reply to slack.",
                                    "trigger": "Get_Log",
                                    "slack_channel": channel,
                                    "input": input_text,
                                    "extracted_email": extracted_email,
                                    "encrypted_email": email,
                                    "token": token,
                                    "date_for_query": str(date_for_query),
                                    "team_id": str(team_id),
                                }
                            )
                            res = ReplyMessage.get_no_log_res(
                                date_for_query.strftime("%Y-%m-%d")
                            )
                            send_to_slack(channel, input_text, res)
                            return "get_log handler success"
                        inference_log["response_body"] = inference_log.apply(
                            lambda x: json.dumps(
                                x["response_body"], ensure_ascii=False
                            ).encode("utf-8"),
                            axis=1,
                        )
                        inference_url = make_log_public(
                            channel,
                            input_text,
                            team_id,
                            date_for_query,
                            inference_log,
                            inference_log_filename,
                        )
                    send_log_to_slack(
                        channel,
                        input_text,
                        team_id,
                        date_for_query.strftime("%Y-%m-%d"),
                        inference_url,
                    )
                    logger.info(
                        {
                            "message": "[Get_Log] Finish get log process.",
                            "trigger": "Get_Log",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "date_for_query": str(date_for_query),
                            "team_id": str(team_id),
                            "inference_url": inference_url,
                        }
                    )
                    return "get_log handler success"
                else:
                    logger.debug(
                        {
                            "message": "[Get_Log] OTP token incorrect. Reply to slack.",
                            "trigger": "Get_Log",
                            "slack_channel": channel,
                            "input": input_text,
                            "extracted_email": extracted_email,
                            "encrypted_email": email,
                            "token": token,
                            "date_for_query": str(date_for_query),
                            "team_info": team_info.to_json(orient="records"),
                        }
                    )
                    res = "您的手機驗證碼輸入錯誤，請再次檢查資訊是否輸入正確！"
            else:
                res = "您尚未使用 register 指令註冊過正式賽，或是您的 email 輸入錯誤，請再次檢查資訊是否輸入正確！"
                logger.debug(
                    {
                        "message": "[Get_Log] Did not find any register log for the team.",
                        "trigger": "Get_Log",
                        "slack_channel": channel,
                        "input": input_text,
                        "extracted_email": extracted_email,
                        "encrypted_email": email,
                        "token": token,
                        "date_for_query": str(date_for_query),
                    }
                )
            conn.commit()
    conn.close()
    send_to_slack(channel, input_text, res)
    logger.info(
        {
            "message": "[Get_Log] Finish get log process.",
            "trigger": "Get_Log",
            "slack_channel": channel,
            "input": input_text,
        }
    )
    return "get_log handler success"


def encrypt_teamid(team_id):
    """
    加密team_id 字串

    Args:
        team_id (string):

    Returns:
        encrypt_team_id: 回傳加密過後的team_id字串
    """
    salt = os.environ["salt"]
    thins_to_encrypt = "esunai" + salt + team_id
    m = hashlib.md5()
    m.update(thins_to_encrypt.encode("utf-8"))
    return m.hexdigest()
