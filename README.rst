.. image:: https://travis-ci.org/yongjhih/locust_mqtt.svg?branch=master
    :target: https://travis-ci.org/yongjhih/locust_mqtt
    :alt: Build Status
.. image:: https://codecov.io/gh/yongjhih/locust_mqtt/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/yongjhih/locust_mqtt

Usage
-----

locustfile.py for example:

.. code:: python

    from locust_mqtt import LocustMqttClient

    class MqttLocust(Locust):
        def __init__(self, *args, **kwargs):
            super(Locust, self).__init__(*args, **kwargs)
            if not self.host:
                self.host: str = "localhost"

            self.client: LocustMqttClient = LocustMqttClient()
            self.client.connect()


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


.. code:: sh

    locust

Installation
------------

.. code:: sh

    python3 -m venv .venv && . .venv/bin/activate
    pip install locust
    pip install git+git://github.com/yongjhih/locust_mqtt.git

Stack
-----

-  unittest(TODO pytest)
-  dataclass PEP 557(python 3.7)
-  Type check PEP 484(python 3.6)
