# -*- coding: utf-8 -*-

import json
import time

from locust import Locust, task, TaskSet, events

from locust_mqtt import LocustMqttClient

class MqttLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(Locust, self).__init__(*args, **kwargs)
        self.client: LocustMqttClient = LocustMqttClient()
        start_time: float = time.time()
        self.client.locust_connect()


class ThingBehavior(TaskSet):
    @task
    def publish_with_qos0(self) -> None:
        topic: str = '#'
        name: str = 'publish:qos0:{}'.format(topic)
        self.client.publish(topic,
                            payload=json.dumps({ 'id': '0' }),
                            qos=0,
                            name=name,
                            timeout=10000)

    def on_start(self) -> None:
        time.sleep(5)


class ThingLocust(MqttLocust):
    task_set: TaskSet = ThingBehavior
