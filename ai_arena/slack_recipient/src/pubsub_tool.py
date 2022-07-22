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
from google.cloud import pubsub_v1


class PubSubOperator:
    """Creates the pubsub object to publish message to specified topic



    Args:
        project_id: project-id google cloud platform
        topic_id:
    """

    def __init__(self, project_id, topic_id):
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = pubsub_v1.PublisherClient()

    def publish_msg(self, message):
        """
        publish_msg _summary_
        Args:
            message(string):
        Return:
            future(future): pubsub returned obj
        Raises:
            None
        """
        topic_path = self.publisher.topic_path(self.project_id, self.topic_id)
        future = self.publisher.publish(topic_path, str(message).encode("utf-8"))
        return future
