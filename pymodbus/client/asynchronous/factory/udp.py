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
    Factory to create twisted udp async client
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and twisted_deferred
    """
    raise NotImplementedError()


def io_loop_factory(host="127.0.0.1", port=Defaults.Port, framer=None,
                   source_address=None, timeout=None, **kwargs):
    """
    Factory to create Tornado based async udp clients
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and tornado future
    """
    from tornado.ioloop import IOLoop
    from pymodbus.client.asynchronous.tornado import AsyncModbusUDPClient as \
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
    """
    Factory to create asyncio based async udp clients
    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: asyncio event loop and udp client
    """
    import asyncio
    from pymodbus.client.asynchronous.asyncio import init_udp_client
    loop = kwargs.get("loop") or asyncio.get_event_loop()
    proto_cls = kwargs.get("proto_cls", None)
    cor = init_udp_client(proto_cls, loop, host, port)
    client = loop.run_until_complete(asyncio.gather(cor))[0]
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

