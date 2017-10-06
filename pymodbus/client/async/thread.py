"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

from threading import Thread

import logging

from tornado.ioloop import IOLoop

LOGGER = logging.getLogger(__name__)


class EventLoopThread(object):
    def __init__(self, name, start, stop, *args, **kwargs):
        self._name = name
        self._start_loop = start
        self._stop_loop = stop
        self._args = args
        self._kwargs = kwargs
        self._event_loop = Thread(name=self._name, target=self._start)

    def _start(self):
        self._start_loop(*self._args, **self._kwargs)

    def start(self):
        LOGGER.info("Starting Event Loop: 'PyModbus_{}'".format(self._name))
        self._event_loop.start()

    def stop(self):
        LOGGER.info("Stopping Event Loop: 'PyModbus_{}'".format(self._name))
        self._stop_loop()
