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
import sys
import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

env = os.environ["ENV"]
logger_name = f'{os.environ["LOGGER_NAME"]}{os.environ["ENV"]}'

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.WARNING)

logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)

if env != "test":
    client = google.cloud.logging.Client()
    gcloud_logging_handler = CloudLoggingHandler(client, name=logger_name)
    logger.addHandler(gcloud_logging_handler)
logger.addHandler(stream_handler)


def logging_generator(*args):
    log_struct = {}
    try:
        for v in args:
            if 'question' in v.keys():
                v.pop('question', None)
            log_struct.update(v)
        return log_struct
    except Exception as e:
        logger.error(f"logging generator failed, error msg: {str(e)}")
