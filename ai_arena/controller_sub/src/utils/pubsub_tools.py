import os
import json
from google.api_core import retry
from src.utils.logger import logger
from google.api_core.exceptions import AlreadyExists
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError


class CallbackOperator():
    def __init__(self, url_dict):
        self.env = os.environ['ENV']
        self.logger = logger
        self.project_id = os.environ['PROJECT_ID']
        self.publisher = pubsub_v1.PublisherClient()
        self.url_dict = url_dict


    def callback_start(self, message):
        msg = {"data":message.data,
               "team_id":message.attributes['team_id'],
               "qid":message.attributes['qid'],
               "slack_channel":message.attributes['slack_channel'],
               "is_verification":message.attributes['is_verification'],
               "verification_id":message.attributes['verification_id'],
               "esun_uuid":message.attributes['esun_uuid'],
               "start":message.attributes['start']}
        self.logger.info({'message': f'[Controller] get qid: {msg["qid"]} for {msg["team_id"]}',
                            'team_id': msg['team_id'],
                            'qid': msg['qid'],
                            'esun_uuid': msg['esun_uuid'],
                            'is_verification': msg['is_verification'],
                            'start': msg['start'],
                            'ENV':self.env})

        message.ack()
        self.publisher = pubsub_v1.PublisherClient()
        topic_path = self.publisher.topic_path(self.project_id, os.environ['SEA_TOPIC'])
        try:
            if msg['team_id'] in list(self.url_dict.keys()):
                future = self.publisher.publish(topic_path, msg['data'],
                                            team_id=msg['team_id'],
                                            qid=msg['qid'],
                                            slack_channel=msg['slack_channel'],
                                            is_verification=msg['is_verification'],
                                            verification_id=msg['verification_id'],
                                            team_url=self.url_dict[msg['team_id']],
                                            start=msg['start'],
                                            esun_uuid=msg['esun_uuid'])

                self.logger.info({'message': f'[Controller] published qid: {msg["qid"]} for {msg["team_id"]}',
                                    'team_id': msg['team_id'],
                                    'qid': msg['qid'],
                                    'esun_uuid': msg['esun_uuid'],
                                    'is_verification': msg['is_verification'],
                                    'start': msg['start'],
                                    'ENV':self.env})
            else:
                self.logger.info({'message': f'[Controller] drop qid: {msg["qid"]} for {msg["team_id"]}',
                                    'team_id': msg['team_id'],
                                    'qid': msg['qid'],
                                    'esun_uuid': msg['esun_uuid'],
                                    'is_verification': msg['is_verification'],
                                    'start': msg['start'],
                                    'ENV':self.env})

        except Exception as error:
            self.logger.error({'message': 'publish task error for qid: {msg["qid"]} for {msg["team_id"]}',
                               'team_id': msg['team_id'],
                               'qid': msg['qid'],
                               'esun_uuid': msg['esun_uuid'],
                               'is_verification': msg['is_verification'],
                               'start': msg['start'],
                               'error_message': str(error),
                               'ENV':self.env})

class PubSubOperator():
    def __init__(self):
        self.env = os.environ['ENV']
        self.logger = logger
        self.project_id = os.environ['PROJECT_ID']
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        self.timeout = int(os.environ['TIMEOUT'])

    def start_task(self, url_dict):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.callback = CallbackOperator(url_dict)
        subscription_path = self.subscriber.subscription_path(self.project_id, f'start-sub-{self.env}')

        streaming_pull_future = self.subscriber.subscribe(
            subscription_path, callback=self.callback.callback_start
        )

        # Wrap subscriber in a 'with' block to automatically call close() when done.
        with self.subscriber:
            try:
                # When `timeout` is not set, result() will block indefinitely,
                # unless an exception is encountered first.
                streaming_pull_future.result(timeout=self.timeout*60)
            except TimeoutError:
                streaming_pull_future.cancel()
                self.logger.info({'message': '[Controller] all start task done',
                                'ENV':self.env})
                raise TimeoutError
            except Exception as error:
                streaming_pull_future.cancel()
                self.logger.error({'message': '[Controller] start task error',
                                'error_message': str(error),
                                'ENV':self.env})
                raise error


    def pull_message(self, qid, team_id, team_url, trigger_time):
        self.subscriber = pubsub_v1.SubscriberClient()
        subscription_id = f'team_{team_id}_{self.env}'
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_id)  
        ack_ids, messages = [], []  
        with self.subscriber:
            # The subscriber pulls a specific number of messages. The actual
            # number of messages pulled may be smaller than max_messages.
            try:
                response = self.subscriber.pull(
                    request={"subscription": subscription_path, "max_messages": 1},
                )
                if not response:
                    if trigger_time < 3:
                        trigger_time+=1
                        self.re_trigger(team_id, qid, team_url, trigger_time)
                        return messages
                    else:
                        self.logger.info({'message':f'[Controller] All task sent',
                                          'team_id':f'{team_id}',
                                          'trigger_time':f'{trigger_time}',
                                          'ENV':self.env})
                        return messages
            except Exception as error:   
                raise error

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
                self.logger.info({'message': f'[Controller] get qid: {msg["qid"]} for team_{msg["team_id"]}',
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
                                'team_id':f'{team_id}',
                                'ENV':self.env})
            except TimeoutError:
                self.logger.info({'message':f'[Controller] There is no task for team_{team_id}_{self.env}',
                                'error_message':f'ack time error for {",".join(str(ack_ids))}',
                                'team_id':f'{team_id}',
                                'ENV':self.env})
                raise RuntimeError(f'[Controller] There is no task for team_{team_id}_{self.env}')
            except Exception as error:
                self.logger.info({'message':f'[Controller] There is no task for team_{team_id}_{self.env}',
                                'error_message':str(error),
                                'ack_id':','.join(str(ack_ids)),
                                'team_id':f'{team_id}',
                                'ENV':self.env})
                raise RuntimeError(f'[Controller] There is no task for team_{team_id}_{self.env}')
        return messages

    def publish_task(self, messages):
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
                raise RuntimeError(error)


    def re_trigger(self, team_id, qid, team_url, trigger_time):
        self.publisher = pubsub_v1.PublisherClient()
        topic_path = self.publisher.topic_path(self.project_id, f'controller-{self.env}')
        self.logger.info({'message':f'[Controller] re trigger next for team_{team_id}',
                           'qid': f'{qid}',
                           'team_id':f'{team_id}',
                           'trigger_time':f'{trigger_time}',
                           'ENV':self.env})
        try:
            future = self.publisher.publish(topic_path, f're trigger to controller'.encode('utf-8'),
                                        team_id=f'{team_id}',
                                        qid=f'{qid}',
                                        team_url=team_url,
                                        trigger_next='Y',
                                        trigger_time=f'{trigger_time}')
            self.logger.info({'message':'[Controller] re trigger message',
                               'team_id': f'{team_id}',
                               'qid': f'{qid}',
                               'trigger_time':f'{trigger_time}',
                               'ENV':f'{self.env}'})
        except Exception as error:
            self.logger.error({'message':f'[Controller] re trigger task failed',
                               'team_id': f'{team_id}',
                               'qid': f'{qid}',
                               'ENV':f'{self.env}',
                               'trigger_time':f'{trigger_time}',
                               'error_message':str(error)})
