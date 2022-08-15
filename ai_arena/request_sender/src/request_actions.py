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
import time
import copy
import requests
from src.log_tool import logger
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter


TIMEOUT_SEC = float(os.environ['call_client_timeout'])


def post_competitors(MO, log_msg):
    """
         post inference request to competitors' server

         parameters:
            MO: MessageOperator instance variable
            log_msg: log message struct
    """

    MO.req_data = copy.deepcopy(MO.msg_data)
    MO.req_data['res_text'] = None
    MO.req_data['retry'] = str(MO.req_data['retry'])
    MO.req_data['esun_timestamp'] = time.time()
    err_msg = None
    try:
        response = requests.post(
            url = f"{MO.msg_attr['team_url']}/inference",
            headers={'Content-Type': 'application/json'},
            json=MO.req_data,
            timeout=TIMEOUT_SEC
        )
        log_msg.update({'message': f"[request_sender]  post competitors finished!"})
        logger.info(log_msg)
        MO.req_data['post_code'] = response.status_code
        if len(response.text) > 10240:
            MO.req_data['res_text'] = str(response.text[0:10240])
        else:
            try:
                MO.req_data['res_text'] = response.json()
            except Exception as error:
                MO.req_data['res_text'] = str(error)
                log_msg.update({
                    'message': f"""
                        [request_sender]  post competitors json decode error: {str(error)}!
                    """})
                logger.error(log_msg)
    except requests.exceptions.InvalidURL as err:
        MO.req_data['post_code'] = 904
        err_msg = err
    except requests.exceptions.InvalidSchema as err:
        MO.req_data['post_code'] = 907
        err_msg = err
    except requests.exceptions.MissingSchema as err:
        MO.req_data['post_code'] = 905
        err_msg = err
    except requests.exceptions.ConnectionError as err:
        MO.req_data['post_code'] = 902
        err_msg = err
    except requests.exceptions.HTTPError as err:
        MO.req_data['post_code'] = 901
        err_msg = err
    except requests.exceptions.Timeout as err:
        MO.req_data['post_code'] = 903
        err_msg = err
    except requests.exceptions.RequestException as err:
        MO.req_data['post_code'] = 900
        err_msg = err
    except ValueError as err:
        MO.req_data['post_code'] = response.status_code
        MO.req_data['res_text'] = {"response_text": str(response.text)}
        log_msg.update({'message': f"""
            [request_sender]  post competitors error msg: {str(err)}
        """})
        logger.error(log_msg)
    finally:
        if err_msg:
            log_msg.update({'message': f"[request_sender]  post competitors error msg: {str(err_msg)}"})
            logger.debug(log_msg)
        MO.req_data['receive_timestamp'] = time.time()
        return MO
