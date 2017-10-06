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
    from twisted.internet import reactor, protocol
    from pymodbus.client.async.twisted import ModbusTcpClientProtocol

    deferred = protocol.ClientCreator(
        reactor, ModbusTcpClientProtocol
    ).connectTCP(host, port, timeout=timeout, bindAddress=source_address)

    callback = kwargs.get("callback")
    errback = kwargs.get("errback")

    if callback:
        deferred.addCallback(callback)

    if errback:
        deferred.addErrback(errback)

    protocol = EventLoopThread("reactor", reactor.run, reactor.stop,
                               installSignalHandlers=0)
    protocol.start()

    return protocol, deferred


def io_loop_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                   source_address=None, timeout=None, **kwargs):
    from tornado.ioloop import IOLoop
    from pymodbus.client.async.tornado import AsyncModbusTCPClient as \
        Client

    ioloop = IOLoop()
    protocol = EventLoopThread("ioloop", ioloop.start, ioloop.stop)
    protocol.start()

    client = Client(host=host, port=port, framer=framer,
                    source_address=source_address,
                    timeout=timeout, ioloop=ioloop, **kwargs)

    future = client.connect()

    return protocol, future


def async_io_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                     source_address=None, timeout=None, **kwargs):
    pass


def get_factory(scheduler):
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    elif scheduler == schedulers.IO_LOOP:
        return io_loop_factory
    elif scheduler == schedulers.ASYNC_IO:
        return async_io_factory
    else:
        LOGGER.warn("Allowed Schedulers: {}, {}, {}".format(
            schedulers.REACTOR, schedulers.IO_LOOP, schedulers.ASYNC_IO
        ))
        raise Exception("Invalid Scheduler '{}'".format(scheduler))
