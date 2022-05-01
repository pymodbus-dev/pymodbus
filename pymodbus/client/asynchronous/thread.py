""" Thread setup. """
from __future__ import unicode_literals
from __future__ import absolute_import

from threading import Thread

import logging

_logger = logging.getLogger(__name__)


class EventLoopThread:
    """ Event loop controlling the backend event loops (io_loop for tornado,
    reactor for twisted and event_loop for Asyncio)
    """
    def __init__(self, name, start, stop, *args, **kwargs):
        """ Initialize Event loop thread
        :param name: Name of the event loop
        :param start: Start method  to start the backend event loop
        :param stop: Stop method to stop the backend event loop
        :param args:
        :param kwargs:
        """
        self._name = name
        self._start_loop = start
        self._stop_loop = stop
        self._args = args
        self._kwargs = kwargs
        self._event_loop = Thread(name=self._name, target=self._start)
        self._event_loop.daemon = True

    def _start(self):
        """ Starts the backend event loop
        :return:
        """
        self._start_loop(*self._args, **self._kwargs)

    def start(self):
        """ Starts the backend event loop
        :return:
        """
        txt = f"Starting Event Loop: 'PyModbus_{self._name}"
        _logger.info(txt)
        self._event_loop.start()

    def stop(self):
        """ Stops the backend event loop
        :return:
        """
        txt = f"Stopping Event Loop: 'PyModbus_{self._name}"
        _logger.info(txt)
        self._stop_loop()
