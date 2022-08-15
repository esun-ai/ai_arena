#!/usr/bin/env python
# Copyright (C) 2022  E.SUN BANK.
# @Author: Tung-Chun Cheng
# @Date: 2022/07
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
from src.utils.logger import logger
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1


class PubSubOperator():
    def __init__(self):
        self.env = os.environ['ENV']
        self.logger = logger
        self.project_id = os.environ['PROJECT_ID']
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        
    
    def publish_team_task(self, teams, start, date):
        """
            Publish message task for teams
            Drop message if failed
            Args:
                teams(list): Today's competitor
                start(str): Start signal
                date(str): competition date, e.g. '2022-06-27'
            Return:
                None
            Raises:
                None
        """
        topic = os.environ['GENERATOR_TOPIC']
        self.publisher = pubsub_v1.PublisherClient()
        topic_path = self.publisher.topic_path(self.project_id, topic)
        for team in teams:
            try:
                future = self.publisher.publish(topic_path,f'publish team for team_id: {team[0]}'.encode('utf-8'),
                                        team_id=f'{team[0]}',
                                        start=f'{start}',
                                        date=str(date))
                self.logger.debug({'message':f'[Controller] published team_{team[0]}.',
                                'team_id':f'{team[0]}',
                                'date': f'{date}',
                                'ENV':f'{self.env}'})
            except:
                self.logger.error({'message':f'[Controller] publish failed for team_{team[0]}.',
                                'team_id':f'{team[0]}',
                                'date': f'{date}',
                                'ENV':f'{self.env}'})

    def create_subscription(self, team_id):
        """
            create subscription for specified team
            Drop message if failed
            Args:
                team_id(str): create subscription of team
            Return:
                None
            Raises:
                RuntimeError: When subscription already created
                error: Unexpected errors
        """
        topic = os.environ['LAKE_TOPIC']
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        subscription_id = f'team_{team_id}_{self.env}'
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)
        topic_path = self.publisher.topic_path(self.project_id, topic)

        try:
            with self.subscriber:
                subscription = self.subscriber.create_subscription(
                        request={'name': subscription_path,
                                'topic': topic_path,
                                'filter':f'attributes.team="{subscription_id}"'}
                        )
            self.logger.info({'message':f'[Controller] create subscription {subscription_id} succeeded',
                            'team':subscription_id,
                            'team_id': team_id,
                            'topic': topic,
                            'ENV':self.env})    
        except AlreadyExists:
            self.logger.error({'message':'[Controller] subscription already exists',
                            'team':subscription_id,
                            'team_id': team_id,
                            'topic': topic,
                            'res_code': 409,
                            'res_message':'supscription already exists',
                            'ENV': self.env})    
            raise RuntimeError('supscription already exists')
        except Exception as error:
            self.logger.error({'message':'[Controller] Unexpected error when create subscription',
                            'team':subscription_id,
                            'team_id': team_id,
                            'topic': topic,
                            'error_message':str(error),
                            'ENV': self.env})    
            raise error

    def get_subscription(self):
        """
            Get subscription in lake topic
            Args:
                None
            Return:
                subscription(list): subscription in lake topic
            Raises:
                error: Unexpected errors
        """
        try:
            self.publisher = pubsub_v1.PublisherClient()
            topic = os.environ['LAKE_TOPIC']
            topic_path = self.publisher.topic_path(self.project_id, topic)
            response = self.publisher.list_topic_subscriptions(request={"topic": topic_path})
            subscription = ','.join([i.split('/')[-1] for i in response])
            return subscription
        except Exception as error:
            self.logger.error({'message':'[Controller] Unexpected error when get subscriptions',
                            'topic': topic,
                            'error_message':str(error),
                            'ENV': self.env})    
            raise error


    def delete_subscription(self, team_id):
        """
            Delete subscription for specified team
            Drop message if failed
            Args:
                team_id(str): create subscription of team
            Return:
                None
            Raises:
                error: Unexpected errors
        """
        try:
            self.subscriber = pubsub_v1.SubscriberClient()
            topic = os.environ['LAKE_TOPIC']
            subscription_id = f'team_{team_id}_{self.env}'
            subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)
            with self.subscriber:
                self.subscriber.delete_subscription(request={"subscription": subscription_path})
            self.logger.info({'message':f'[Controller] delete subscription {subscription_id} succeeded',
                                'team':subscription_id,
                                'team_id': team_id,
                                'ENV':self.env})
        except Exception as error:
            self.logger.error({'message':'[Controller] Unexpected error when delete subscriptions',
                            'topic': topic,
                            'error_message':str(error),
                            'ENV': self.env})    
            raise error

    def pull_message(self, team_id, team_url):
        """
            Pull message from  subscription of specified team
            Args:
                team_id(str): create subscription of team
                team_url(string): team api url e.g. 10.0.0.1:8080
            Return:
                None
            Raises:
                RuntimeError: Subscription not found
                error: Unexpected errors
        """
        self.subscriber = pubsub_v1.SubscriberClient()
        subscription_id = f'team_{team_id}_{self.env}'
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)    
        with self.subscriber:
            # The subscriber pulls a specific number of messages. The actual
            # number of messages pulled may be smaller than max_messages.
            try:
                response = self.subscriber.pull(
                    request={"subscription": subscription_path, "max_messages": 1},
                )
            except:   
                raise RuntimeError(f"Subscription for {subscription_id} not found.")

            ack_ids, messages = [], []
            for received_message in response.received_messages:
                message = received_message.message
                ack_ids += [received_message.ack_id]
                msg = {"data":message.data,
                       "team_id":message.attributes['team_id'],
                       "team_url":team_url,
                       "qid":message.attributes['qid'],
                       "slack_channel":message.attributes['slack_channel'],
                       "is_verification":message.attributes['is_verification'],
                       "verification_id":message.attributes['verification_id'],
                       "esun_uuid":message.attributes['esun_uuid'],
                       "start":message.attributes['start']}
                self.logger.info({'message': f'[Controller] get qid: {msg["qid"]} for team_{msg["team_id"]}, question: {msg["data"]}',
                                    'team_id': msg['team_id'],
                                    'qid': msg['qid'],
                                    'esun_uuid': msg['esun_uuid'],
                                    'is_verification': msg['is_verification'],
                                    'start': msg['start'],
                                    'ENV': self.env})    
                messages += [msg]

            try:
                self.subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
                self.logger.info({'message':'[Controller] pull message succeeded',
                                'team':subscription_id,
                                'ENV':self.env})    
            except Exception as error:
                raise RuntimeError(f"pull verify task for team {subscription_id} failed. error message: {error}")  
        return messages

    def publish_verify_task(self, messages):
        """
            Publish message to sea topic
            Args:
                message(list): list of send messages
            Return:
                None
            Raises:
                RuntimeError: Subscription not found
                error: Unexpected errors
        """
        self.publisher = pubsub_v1.PublisherClient()
        topic = sea_topic = os.environ['SEA_TOPIC']
        topic_path = self.publisher.topic_path(self.project_id, topic)
        for msg in messages:
            try:
                future = self.publisher.publish(topic_path, msg['data'],
                                            team_id=msg['team_id'],
                                            qid=msg['qid'],
                                            slack_channel=msg['slack_channel'],
                                            is_verification=msg['is_verification'],
                                            verification_id=msg['verification_id'],
                                            team_url=msg['team_url'],
                                            esun_uuid=msg['esun_uuid'],
                                            start=msg['start'])
                self.logger.info({'message':'[Controller] published message',
                                'team_id': msg['team_id'],
                                'qid': msg['qid'],
                                'esun_uuid': msg['esun_uuid'],
                                'is_verification': msg['is_verification'],
                                'start': msg['start'],
                                'message_id': future.result(),
                                'ENV':self.env})    
            except Exception as error:    
                raise RuntimeError(f"publish verify task for team {msg['team_id']} failed. error message: {error}")
