# -*- coding: utf-8 -*-

import json
import time

from locust import Locust, task, TaskSet, events

from locust_mqtt import LocustMqttClient

class MqttLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(Locust, self).__init__(*args, **kwargs)
        if not self.host:
            self.host: str = "localhost"

        self.client: LocustMqttClient = LocustMqttClient()
        start_time: float = time.time()

        try:
            # It is important to do an asynchronous connect, given that we will have
            # multiple connections happening in a single server during a Locust test
            self.client.connect_async(self.host, 1883)
            self.client.loop_start()
        except Exception as e:
            events.request_failure.fire(
                request_type='MQTT',
                name='connect',
                response_time=int(start_time - time.time()) * 1000,
                exception=e
            )


class ThineBehavior(TaskSet):
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


class ThineLocust(MqttLocust):
    task_set: TaskSet = ThingBehavior
