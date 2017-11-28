"""
Copyright (c) 2017 by Riptide I/O
All rights reserved.
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.async import schedulers
from pymodbus.client.async.thread import EventLoopThread
from pymodbus.constants import Defaults

LOGGER = logging.getLogger(__name__)


def reactor_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                    source_address=None, timeout=None, **kwargs):
    raise NotImplementedError()


def io_loop_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                   source_address=None, timeout=None, **kwargs):
    from tornado.ioloop import IOLoop
    from pymodbus.client.async.tornado import AsyncModbusUDPClient as \
        Client

    client = Client(host=host, port=port, framer=framer,
                    source_address=source_address,
                    timeout=timeout, **kwargs)
    protocol = EventLoopThread("ioloop", IOLoop.current().start,
                               IOLoop.current().stop)
    protocol.start()
    future = client.connect()

    return protocol, future


def async_io_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                     source_address=None, timeout=None, **kwargs):
    raise NotImplementedError()


def get_factory(scheduler):
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    elif scheduler == schedulers.IO_LOOP:
        return io_loop_factory
    elif scheduler == schedulers.ASYNC_IO:
        return async_io_factory
    else:
        LOGGER.warning("Allowed Schedulers: {}, {}, {}".format(
            schedulers.REACTOR, schedulers.IO_LOOP, schedulers.ASYNC_IO
        ))
        raise Exception("Invalid Scheduler '{}'".format(scheduler))

