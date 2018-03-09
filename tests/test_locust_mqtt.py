# -*- coding: utf-8 -*-

import pytest

import json
import time

from locust import Locust, task, TaskSet, events

from locust_mqtt import LocustMqttClient

#def test_locust_mqtt():
#    self.client: LocustMqttClient = LocustMqttClient()
