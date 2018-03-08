Usage
-----

For example of locustfile.py:

.. code:: python

    from mqtt_locust import LocustMqttClient

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
                fire_locust_failure(
                    request_type=REQUEST_TYPE,
                    name='connect',
                    response_time=time_delta(start_time, time.time()),
                    exception=ConnectError("Could not connect to host:[" + self.host + "]")
                )


    class FloDeviceBehavior(TaskSet):
        @task
        def publish_with_qos0(self) -> None:
            thing: Thing = Thing.random()
            topic: str = '#'
            name: str = 'publish:qos0:{}'.format(topic)
            self.client.publish(topic,
                                payload=thing.json(),
                                qos=0,
                                name=name,
                                timeout=10000)

        def on_start(self) -> None:
            time.sleep(5)


    @dataclass
    class Thing:
        device_id: str

        @classmethod
        def random(cls):
            return cls(
                id = ''.join(map(lambda x: "%02x" % x, [0x00, 0x16, 0x3e,
                          random.randint(0x00, 0x7f),
                          random.randint(0x00, 0xff),
                          random.randint(0x00, 0xff)]))
            )

        def json(self) -> str:
            return json.dumps({
                'id': self.id
            })


    class FloDeviceLocust(MqttLocust):
        task_set: TaskSet = ThingBehavior


.. code:: sh

    locust

Installation
------------

.. code:: sh

    python3 -m venv .venv && . .venv/bin/activate
    pip install locust
    pip install git+git://github.com/yongjhih/locust-mqtt.git

Stack
-----

-  unittest(TODO pytest)
-  dataclass PEP 557(python 3.7)
-  Type check PEP 484(python 3.6)
