#!/usr/bin/env python
# Copyright (C)  E.SUN BANK
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
import re
import validators
from datetime import datetime
import pytz
import bcrypt
from urllib.parse import urlparse

tw = pytz.timezone("Asia/Taipei")
utc = pytz.utc


def extract_email(email_str):
    if email_str.startswith("[") and email_str.endswith("]"):
        email = email_str[1:-1]
    elif "<mailto:" in email_str:
        email = email_str.split("|")[1][:-1]
    else:
        email = email_str
    return email


def extract_token(token_str):
    if token_str.startswith("[") and token_str.endswith("]"):
        token = token_str[1:-1]
    else:
        token = token_str
    return token


def encrypt_email(email_str):
    SALT = os.environ["salt"].encode()
    return bcrypt.hashpw(bytes(email_str, "ascii"), SALT).decode("ascii")


def extract_url(api_url_str):
    if api_url_str.startswith("[") and api_url_str.endswith("]"):
        api_url_str = api_url_str[1:-1]
    if "<" in api_url_str and ">" in api_url_str:
        api_url_str = api_url_str[api_url_str.index("<") + 1 : api_url_str.index(">")]
    o = urlparse(api_url_str)
    if o.scheme:
        if "|" in api_url_str:
            api_url = api_url_str.split("|")[1]
        else:
            api_url = api_url_str
    else:
        api_url = "http://" + api_url_str
    return api_url


def get_now_timestamp():
    dt = datetime.now()
    utc_dt = utc.localize(dt)
    now_timestamp = utc_dt.astimezone(tw)
    return now_timestamp


def email_format_match(mail):
    EMAIL_REGEX = re.compile(r"[A-Za-z\.\_\-0-9\+]+@[A-Za-z\_\-\.0-9]+\.[A-Za-z\.0-9]+")
    mail = extract_email(mail)
    return bool(EMAIL_REGEX.match(mail))


def token_format_match(token):
    TOKEN_REGEX = re.compile(r"^\d{6}$")
    token = extract_token(str(token))
    return bool(TOKEN_REGEX.match(token))


def check_url_valid(api_url):
    if api_url.startswith("[") and api_url.endswith("]"):
        api_url = api_url[1:-1]
    o = urlparse(api_url)
    match = re.search(":([0-9]+)", o.netloc)
    if match:
        if int(match[0].split(":")[1]) > 65535:
            return False
    return bool(validators.url(api_url))
