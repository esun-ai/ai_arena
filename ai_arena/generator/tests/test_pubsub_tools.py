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

from google.cloud import pubsub_v1
import pytest
from unittest.mock import patch
from src.pubsub_tools import publish_task


@pytest.fixture()
def questions():
    return [('1', 'base64image1'), ('2', 'base64image2'), ('3', 'base64image3')]


@patch('google.cloud.pubsub_v1.PublisherClient')
def test_pubsub_client(MockPublisherClient, questions):
    mock_publisher_return = MockPublisherClient.return_value
    failed_task = publish_task(questions, '13', 'Y')
    MockPublisherClient.assert_called_once()
    mock_publisher_return.topic_path.assert_called_once()
    assert mock_publisher_return.publish.call_count == len(questions)
    assert failed_task == []


@patch('google.cloud.pubsub_v1.PublisherClient.publish')
def test_publish_fail(MockPublish, questions):
    team_id = '13'
    start = 'Y'
    MockPublish.side_effect = Exception('raise error') 
    failed_task = publish_task(questions, team_id, start)
    assert len(failed_task) == len(questions)
    # Each element in faild_task should be ordered as [qid, team, data, start, esun_uuid]
    # assert failed_task[0][0:4] == [questions[0][0], '13', questions[0][1], start]
    assert failed_task[0][0:2] == [questions[0][0], '13']
