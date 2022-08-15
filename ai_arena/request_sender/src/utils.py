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
import json
import numbers
import requests
from src.log_tool import logger
from datetime import datetime, timedelta
from src.db_tools import DBOperator as DBO


SLACK_URL = os.environ['slack_url']
SLACK_BOT_TOKEN = os.environ['slack_bot_token']


def check_competitors_response(RO, log_msg):
    """
        Check if the response format and data type
        from competitors is correct or not.

        parameters:
            MO: MessageOperator instance variable
            log_msg: log message struct
    """
    check_text = RO.req_data['res_text']
    if not isinstance(check_text, dict):
        return False
    necessary_key_list = ['esun_uuid','server_uuid','answer','server_timestamp']
    for key in check_text.keys():
        if key not in necessary_key_list:
            print('{} not in response'.format(key))
            return False
        if key == 'server_timestamp':
            if not isinstance(check_text[key], numbers.Number):
                return False
        else:
            if not isinstance(check_text[key], str):
                return False
    log_msg.update({'message': f"[request_sender]  check_competitors_response finished!"})
    logger.info(log_msg)
    return True
    

def send_to_slack(slack_type, MO, log_msg):
    """
        Depending on the verification result,
        send the correspondent response to slack.

        parameters:
            slack_type: correspondent slack response message
                depending on post_code and competitors response format
            MO: MessageOperator instance variable
            log_msg: log message struct
    """
    slack_response = {
        '0': f"驗證結果通知: inference api 回傳格式錯誤，您回傳的資訊為 {MO.req_data['res_text']}",
        '1': "驗證結果通知: inference api 成功",
        '900': f"驗證結果通知: inference階段失敗, 您的伺服器無回應, 請確認是否開啟, 剩餘retry 次數: {MO.msg_data['retry']}",
        '901': f"驗證結果通知: inference階段失敗, 從您的api提取回應失敗, 請確認服務已啟用, 剩餘retry 次數: {MO.msg_data['retry']}",
        '902': f"驗證結果通知: inference階段失敗, 連線失敗, 請確認您的網路狀態是否正常, 剩餘retry 次數: {MO.msg_data['retry']}",
        '903': f"驗證結果通知: inference階段失敗, 連線逾時, 請確認是否在時間內回傳, 剩餘retry 次數: {MO.msg_data['retry']}",
        '904': f"驗證結果通知: inference階段失敗, 您的api url格式錯誤, 請檢查後重新驗證, 剩餘retry 次數: {MO.msg_data['retry']}",
        'else': f"驗證結果通知: inference 回傳status為 {slack_type}, 預期為 200, 剩餘retry 次數: {MO.msg_data['retry']}"
    }
    if slack_response.get(slack_type):
        response = slack_response[slack_type]
    else:
        response = slack_response['else']

    slack_content = {
        'token': SLACK_BOT_TOKEN,
        'as_user': True,
        'channel': MO.msg_attr['slack_channel'],
        'text': response
    }
    try:
        res = requests.post(SLACK_URL, data=slack_content)
        if res.status_code != 200:
            log_msg.update({
                'message': f"""[request_sender]  send to slack failed!
                status code: {str(res.status_code)},
                slack error msg: {str(res.text)}"""
            })
            logger.error(log_msg)
        elif res.json().get('ok') == False:
            log_msg.update({'message': f"""[request_sender]  send to slack failed!
                slack error msg: {res.json()}"""})
            logger.error(log_msg)
        elif res.json().get('ok') == True:
            log_msg.update({'message': f"[request_sender]  send to slack success!"})
            logger.info(log_msg)
        else:
            log_msg.update({'message': f"""[request_sender]  send to slack failed!
                slack error msg: {str(res.text)}"""})
            logger.error(log_msg)
    except Exception as e:
        log_msg.update({'message': f"[request_sender]  send to slack failed!"})
        logger.error(log_msg)


def verification_processor(MO, log_msg):
    """
        Verification processor: including check response,
        update verification table and send message to slack.

        parameters:
            MO: MessageOperator instance variable
            log_msg: log message struct
    """
    try:
        if MO.req_data['post_code'] == 200:
            check_result = check_competitors_response(MO, log_msg)
            if check_result:
                slack_type = 1
            else:
                slack_type = 0
        else:
            slack_type = MO.req_data['post_code']
        DB_HOOK = DBO(log_msg)
        DB_HOOK.update_verification(MO.req_data['post_code'], MO.msg_attr['verification_id'])
        send_to_slack(str(slack_type), MO, log_msg)
        log_msg.update({'message': f"[request_sender]  verification processor success!"})
        logger.info(log_msg)
    except Exception as e:
        log_msg.update({'message': f"""[request_sender]  verification processor failed! 
            error msg: {str(e)}"""})
        logger.error(log_msg)


def answer_response_processor(MO, log_msg):
    """
        Competitor response processor: depending on different
        post code, give variable different value.

        parameters:
            MO: MessageOperator instance variable
            log_msg: log message struct
    """
    try:
        if MO.req_data['post_code'] == 200:
            check_result = check_competitors_response(MO)
            if check_result:
                answer = MO.req_data['res_text']['answer']
                get_time = MO.req_data['res_text']['server_timestamp']
                status_code = MO.req_data['post_code']
                text = json.dumps(MO.req_data['res_text'], ensure_ascii=False)
                u_uuid = MO.req_data['res_text']['server_uuid']
            else:
                answer = 'fail'
                get_time = 99999999999
                status_code = 999
                text = json.dumps(MO.req_data['res_text'], ensure_ascii=False)
                u_uuid = 'the body of response was wrong'   
        else:
            answer = 'fail'
            get_time = 99999999999
            status_code = MO.req_data['post_code']
            text = json.dumps('fail', ensure_ascii=False)
            u_uuid = 'fail'

        post_time = datetime.utcfromtimestamp(
            MO.req_data['esun_timestamp']
        ) + timedelta(hours=8)
        receive_timestamp = datetime.utcfromtimestamp(
            MO.req_data['receive_timestamp']
        ) + timedelta(hours=8)
        answer_list = (
            MO.msg_attr['qid'], answer, MO.team_id,
            post_time,
            get_time, status_code, MO.msg_data['retry'], text,
            MO.msg_attr['esun_uuid'], u_uuid,
            receive_timestamp
        )
        DB_HOOK = DBO(log_msg)
        DB_HOOK.insert_answer(answer_list)
        log_msg.update({'message': f"[request_sender]  answer_response_processor success"})
        logger.info(log_msg)
    except Exception as e:
        log_msg.update({
            'message': f"""[request_sender]  answer_response_processor failed!
            error msg: {str(e)}
        """})
        logger.error(log_msg)
