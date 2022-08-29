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
import pytest
from google.cloud import pubsub_v1

# PROJECT = "if-aicompetition"
# TOPIC = "slack_msg"

# assert PROJECT is not None
# assert TOPIC is not None

from app import app

slack_post_data = [
    ({"challenge": "challenge_pytest"}, "challenge_pytest"),
]


@pytest.fixture(scope="module")
def publisher_client():
    yield pubsub_v1.PublisherClient()


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_healthcheck(client, mocker):
    mocker.patch.object(app, "before_request_funcs", {})
    response = client.get("/health")
    assert "I'm good" in response.text


@pytest.mark.parametrize("test_input,expected", slack_post_data)
def test_slack_webhook(client, mocker, test_input, expected):
    mocker.patch.object(app, "before_request_funcs", {})
    response = client.post("/webhook", json=test_input)
    assert response.text == expected
