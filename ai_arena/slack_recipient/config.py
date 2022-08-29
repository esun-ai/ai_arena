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


class Base:
    DEBUG = False
    TESTING = False
    LOGGER_NAME = os.environ["LOGGER_NAME"]
    SLACK_BOT_TOKEN = ""
    SLACK_URL = "https://slack.com/api/chat.postMessage"


class ProductionConfig(Base):
    DEBUG = False
    PROJECT_ID = os.environ["PROJECT_ID"]
    VERIFICATION_ROUND = -1
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_SIGN_SECRET = os.environ["SLACK_SIGN_SECRET"]


class DevelopmentConfig(Base):
    DEBUG = True
    PROJECT_ID = os.environ["PROJECT_ID"]
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_SIGN_SECRET = os.environ["SLACK_SIGN_SECRET"]


class TestConfig(Base):
    DEBUG = True
    TESTING = True
    PROJECT_ID = "Test"
    SLACK_BOT_TOKEN = ""
    SLACK_SIGN_SECRET = ""
