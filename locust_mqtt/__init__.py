# -*- coding: utf-8 -*-

import time
import ssl

import paho.mqtt.client as mqtt
from locust import Locust, task, TaskSet, events
from typing import Any, Callable, Dict, List, Optional, Union

REQUEST_TYPE: str = 'MQTT'
MESSAGE_TYPE_PUB: str = 'PUB'
MESSAGE_TYPE_SUB: str = 'SUB'

def error_message(error: int) -> str:
  if error == mqtt.MQTT_ERR_AGAIN:
    return "MQTT_ERR_AGAIN"
  if error == mqtt.MQTT_ERR_SUCCESS:
    return "MQTT_ERR_SUCCESS"
  if error == mqtt.MQTT_ERR_NOMEM:
    return "MQTT_ERR_NOMEM"
  if error == mqtt.MQTT_ERR_PROTOCOL:
    return "MQTT_ERR_PROTOCOL"
  if error == mqtt.MQTT_ERR_INVAL:
    return "MQTT_ERR_INVAL"
  if error == mqtt.MQTT_ERR_NO_CONN:
    return "MQTT_ERR_NO_CONN"
  if error == mqtt.MQTT_ERR_CONN_REFUSED:
    return "MQTT_ERR_CONN_REFUSED"
  if error == mqtt.MQTT_ERR_NOT_FOUND:
    return "MQTT_ERR_NOT_FOUND"
  if error == mqtt.MQTT_ERR_CONN_LOST:
    return "MQTT_ERR_CONN_LOST"
  if error == mqtt.MQTT_ERR_TLS:
    return "MQTT_ERR_TLS"
  if error == mqtt.MQTT_ERR_PAYLOAD_SIZE:
    return "MQTT_ERR_PAYLOAD_SIZE"
  if error == mqtt.MQTT_ERR_NOT_SUPPORTED:
    return "MQTT_ERR_NOT_SUPPORTED"
  if error == mqtt.MQTT_ERR_AUTH:
    return "MQTT_ERR_AUTH"
  if error == mqtt.MQTT_ERR_ACL_DENIED:
    return "MQTT_ERR_ACL_DENIED"
  if error == mqtt.MQTT_ERR_UNKNOWN:
    return "MQTT_ERR_UNKNOWN"
  if error == mqtt.MQTT_ERR_ERRNO:
    return "MQTT_ERR_ERRNO"
  if error == mqtt.MQTT_ERR_QUEUE_SIZE:
    return "MQTT_ERR_QUEUE_SIZE"
  return str(error)


def time_delta(t1: float, t2: float) -> int:
    return int((t2 - t1) * 1000)


def fire_locust_failure(**kwargs) -> None:
    events.request_failure.fire(**kwargs)


def fire_locust_success(**kwargs) -> None:
    events.request_success.fire(**kwargs)


class LocustError(Exception):
    pass


class TimeoutError(ValueError):
    pass


class ConnectError(Exception):
    pass


class DisconnectError(Exception):
    pass


class Message(object):
    def __init__(self, type: str, qos: int, topic: str, payload: str, start_time: float, timeout: int, name: str):
        self.type = type,
        self.qos = qos,
        self.topic = topic
        self.payload = payload
        self.start_time = start_time
        self.timeout = timeout
        self.name = name

    def timed_out(self, total_time: int) -> bool:
        return bool(self.timeout) and total_time > self.timeout


class LocustMqttClient(mqtt.Client):
    def __init__(self, *args, **kwargs):
        super(LocustMqttClient, self).__init__(*args, **kwargs)
        self.on_publish = self.locust_on_publish
        self.on_subscribe = self.locust_on_subscribe
        self.on_disconnect = self.locust_on_disconnect
        self.on_connect = self.locust_on_connect
        # {mid: message}
        self.pubmmap = {}
        # {mid: message}
        self.submmap = {}
        self.defaultQoS: int = 0

    def tls_set(self,
                ca_certs,
                certfile: Optional[str] = None,
                keyfile: Optional[str] = None,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None):
        start_time: float = time.time()
        try:
            super(LocustMqttClient, self).tls_set(ca_certs,
                                            certfile,
                                            keyfile,
                                            cert_reqs,
                                            tls_version,
                                            ciphers)
        except Exception as e:
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name='tls_set',
                response_time=time_delta(start_time, time.time()),
                exception=e,
                response_length=0
            )

    # retry is not used at the time since this implementation only supports QoS 0
    def publish(self, topic: str, payload: Optional[str] = None, qos: int = 0, retry: int = 5, name: str = 'publish',
                **kwargs) -> None:
        timeout: int = kwargs.pop('timeout', 10000)
        start_time: float = time.time()
        try:
            # print(topic)
            # print(payload)
            # (result: int, mid: int)
            # MQTT_ERR_SUCCESS to indicate success, or (MQTT_ERR_NO_CONN)
            err, mid = super(LocustMqttClient, self).publish(
                topic,
                payload=payload,
                qos=qos,
                **kwargs
            )
            if err:
                fire_locust_failure(
                    request_type=REQUEST_TYPE,
                    name=name,
                    response_time=time_delta(start_time, time.time()),
                    exception=ValueError(error_message(err)),
                    response_length = 0
                )

                #print("publish: err,mid:[" + error_message(err) + "," + str(mid) + "]")
            self.pubmmap[mid] = Message(
                MESSAGE_TYPE_PUB, qos, topic, payload, start_time, timeout, name
            )
        except Exception as e:
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=name,
                response_time=time_delta(start_time, time.time()),
                exception=e,
                response_length=0
            )
            #print(str(e))

    # retry is not used at the time since this implementation only supports QoS 0
    def subscribe(self, topic: str, qos: int = 0, retry: int = 5, name: str = 'subscribe', timeout: int = 15000):
        # print ("subscribing to topic:["+topic+"]")
        start_time: float = time.time()
        try:
            err, mid = super(LocustMqttClient, self).subscribe(
                topic,
                qos=qos
            )
            self.submmap[mid] = Message(
                MESSAGE_TYPE_SUB, qos, topic, "", start_time, timeout, name
            )
            if err:
                raise ValueError(error_message(err))
                #print("Subscribed to topic with err:[" + error_message(err) + "]messageId:[" + str(mid) + "]")
        except Exception as e:
            total_time: int = time_delta(start_time, time.time())
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=name,
                response_time=total_time,
                exception=e,
                response_length=0
            )
            #print("Exception when subscribing to topic:[" + str(e) + "]")

    def locust_on_connect(self, client: mqtt.Client, flags_dict, userdata, rc) -> None:
        # print("Connection returned result: "+mqtt.connack_string(rc))
        fire_locust_success(
            request_type=REQUEST_TYPE,
            name='connect',
            response_time=0,
            response_length=0
        )

    """
    Paho documentation regarding on_publish event:
    'For messages with QoS levels 1 and 2, this means that the appropriate handshakes have
    completed. For QoS 0, this simply means that the message has left the client.'

    This means that the value we record in fire_locust_success for QoS 0 will always
    be very low and not a meaningful metric. The interesting part comes when we analyze
    metrics emitted by the system on the other side of the MQTT broker (the systems processing
    incoming data from things).
    """

    def locust_on_publish(self, client: mqtt.Client, userdata, mid: int):
        end_time: float = time.time()

        if self.defaultQoS == 0:
            # if QoS=0, we reach the callback before the publish() has enough time to update the pubmmap dictionary
            time.sleep(float(0.5))

        message: Message = self.pubmmap.pop(mid, None)
        # print ("on_publish  - mqtt client obj id:["+str(id(self))+"] - pubmmap obj id:["+str(id(self.pubmmap))+"] - mid:["+str(mid)+"] - message obj id:["+str(id(message))+"]")
        if not message:
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name="message_found",
                response_time=0,
                exception=ValueError("Published message could not be found"),
                response_length=0
            )
            return

        total_time: int = time_delta(message.start_time, end_time)
        if message.timed_out(total_time):
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                exception=TimeoutError("publish timed out"),
                response_length=len(message.payload),
            )
            # print("report publish failure - response_time:["+str(total_time)+"]")
        else:
            fire_locust_success(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                response_length=len(message.payload),
            )
            # print("report publish success - response_time:["+str(total_time)+"]")

    def locust_on_subscribe(self, client: mqtt.Client, userdata, mid: int, granted_qos):
        end_time: float = time.time()
        message: Message = self.submmap.pop(mid, None)
        if not message:
            # print("Not found message for on_subscribe")
            return
        total_time: int = time_delta(message.start_time, end_time)
        if message.timed_out(total_time):
            fire_locust_failure(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                exception=TimeoutError("subscribe timed out"),
                response_length=len(message.payload),
            )
            # print("report subscribe failure - response_time:[" + str(total_time) + "]")
        else:
            fire_locust_success(
                request_type=REQUEST_TYPE,
                name=message.name,
                response_time=total_time,
                response_length=0,
            )
            # print("report subscribe success - response_time:[" + str(total_time) + "]")

    def locust_on_disconnect(self, client: mqtt.Client, userdata, rc):
        fire_locust_failure(
            request_type=REQUEST_TYPE,
            name='disconnect',
            response_time=0,
            exception=DisconnectError("disconnected"),
            response_length=0,
        )
        self.reconnect()

    def locust_connect(self, host: str = 'localhost', port: int = 1883):
        start_time: float = time.time()
        try:
            self.connect_async(host, port)
            self.loop_start()
        except Exception as e:
            events.request_failure.fire(
                request_type='MQTT',
                name='connect',
                response_time=int(start_time - time.time()) * 1000,
                exception=e,
                response_length=0,
            )

