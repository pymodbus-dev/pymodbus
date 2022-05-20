"""UDP implementation."""
import logging
import asyncio

from pymodbus.client.asynchronous.async_io import init_udp_client
from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


def reactor_factory(
    host="127.0.0.1",
    port=Defaults.Port,
    framer=None,
    source_address=None,
    timeout=None,
    **kwargs,
):
    """Create twisted udp asynchronous client.

    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and twisted_deferred
    """
    raise NotImplementedError()


def io_loop_factory(
    host="127.0.0.1",
    port=Defaults.Port,
    framer=None,
    source_address=None,
    timeout=None,
    **kwargs,
):
    """Create Tornado based asynchronous udp clients.

    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and tornado future
    """
    from tornado.ioloop import IOLoop  # pylint: disable=import-outside-toplevel
    from pymodbus.client.asynchronous.tornado import (  # pylint: disable=import-outside-toplevel
        AsyncModbusUDPClient as Client,
    )

    client = Client(
        host=host,
        port=port,
        framer=framer,
        source_address=source_address,
        timeout=timeout,
        **kwargs,
    )
    protocol = EventLoopThread("ioloop", IOLoop.current().start, IOLoop.current().stop)
    protocol.start()
    future = client.connect()

    return protocol, future


def async_io_factory(host="127.0.0.1", port=Defaults.Port, **kwargs):
    """Create asyncio based asynchronous udp clients.

    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: asyncio event loop and udp client
    """
    try:
        loop = kwargs.pop("loop", None) or asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    proto_cls = kwargs.pop("proto_cls", None)
    cor = init_udp_client(proto_cls, loop, host, port, **kwargs)
    if not loop.is_running():
        cor = init_udp_client(proto_cls, loop, host, port)
        client = loop.run_until_complete(asyncio.gather(cor))[0]
    elif loop is asyncio.get_event_loop():
        return loop, init_udp_client(proto_cls, loop, host, port)

    cor = init_udp_client(proto_cls, loop, host, port)
    client = asyncio.run_coroutine_threadsafe(cor, loop=loop)
    client = client.result()

    return loop, client


def get_factory(scheduler):
    """Get protocol factory based on the backend scheduler being used.

    :param scheduler: REACTOR/IO_LOOP/ASYNC_IO
    :return
    """
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    if scheduler == schedulers.IO_LOOP:
        return io_loop_factory
    if scheduler == schedulers.ASYNC_IO:
        return async_io_factory

    txt = f"Allowed Schedulers: {schedulers.REACTOR}, {schedulers.IO_LOOP}, {schedulers.ASYNC_IO}"
    _logger.warning(txt)
    txt = f'Invalid Scheduler "{scheduler}"'
    raise Exception(txt)
