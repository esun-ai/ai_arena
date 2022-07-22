#
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

# -*- coding: UTF-8 -*-
import os
from google.cloud import pubsub_v1
from src.slack_utils import send_to_slack
from src.slack_event import SlackEventMessage
import src.slack_command_processor as slack_proc
from src.logger import logger
from src.slack_bot_reply_msg import ReplyMessage

project_id = os.environ["PROJECT_ID"]
subscription_id = f"slack-msg-consumer-{os.environ['ENV']}"
logger.info("slack msg consumer start logging...")


def callback(message):
    slack_event = SlackEventMessage(message.data.decode("utf-8"))
    try:
        if slack_event.user_purpose == "forget_token":
            exec_result = slack_proc.forget_token_handler(
                slack_event.channel_id, slack_event.text_msg_list
            )
        elif slack_event.user_purpose == "register":
            exec_result = slack_proc.register_handler(
                slack_event.channel_id, slack_event.text_msg_list
            )
        elif slack_event.user_purpose == "verification":
            exec_result = slack_proc.verification_handler(
                slack_event.channel_id, slack_event.text_msg_list
            )
        elif slack_event.user_purpose == "get_status":
            exec_result = slack_proc.get_status_handler(
                slack_event.channel_id, slack_event.text_msg_list
            )
        elif slack_event.user_purpose == "get_log":
            exec_result = slack_proc.get_log_handler(
                slack_event.channel_id, slack_event.text_msg_list
            )
        else:
            send_to_slack(
                slack_event.channel_id,
                str(slack_event.user_purpose),
                f" {ReplyMessage.USAGE_GUIDE}",
            )
    except Exception as e:
        send_to_slack(
            slack_event.channel_id,
            str(slack_event.user_purpose),
            ReplyMessage.SYSTEM_ERROR,
        )
        logger.error(f"slack msg processing error: {e}")
    message.ack()


def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    logger.info(f"Listening for messages on {subscription_path}..\n")

    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            logger.info(f"straming pull with msg-id: {streaming_pull_future.result()}")
        except TimeoutError:
            logger.warning("subscriber timeout", exc_info=True)
            streaming_pull_future.cancel()


if __name__ == "__main__":
    main()
