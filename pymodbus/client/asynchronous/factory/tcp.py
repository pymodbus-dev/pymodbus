"""
Factory to create asynchronous tcp clients based on twisted/tornado/asyncio
"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread
from pymodbus.constants import Defaults

LOGGER = logging.getLogger(__name__)


def reactor_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                    source_address=None, timeout=None, **kwargs):
    """
    Factory to create twisted tcp asynchronous client
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and twisted_deferred
    """
    from twisted.internet import reactor, protocol
    from pymodbus.client.asynchronous.twisted import ModbusTcpClientProtocol

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
    """
    Factory to create Tornado based asynchronous tcp clients
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and tornado future
    """
    from tornado.ioloop import IOLoop
    from pymodbus.client.asynchronous.tornado import AsyncModbusTCPClient as \
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
    """
    Factory to create asyncio based asynchronous tcp clients
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: asyncio event loop and tcp client
    """
    import asyncio
    from pymodbus.client.asynchronous.async_io import init_tcp_client
    loop = kwargs.get("loop") or asyncio.new_event_loop()
    proto_cls = kwargs.get("proto_cls", None)
    if not loop.is_running():
        asyncio.set_event_loop(loop)
        cor = init_tcp_client(proto_cls, loop, host, port)
        client = loop.run_until_complete(asyncio.gather(cor))[0]
    else:
        cor = init_tcp_client(proto_cls, loop, host, port)
        future = asyncio.run_coroutine_threadsafe(cor, loop=loop)
        client = future.result()

    return loop, client


def get_factory(scheduler):
    """
    Gets protocol factory based on the backend scheduler being used
    :param scheduler: REACTOR/IO_LOOP/ASYNC_IO
    :return
    """
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
