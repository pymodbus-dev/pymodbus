"""Factory to create asynchronous tcp clients based on twisted/asyncio."""
# pylint: disable=missing-type-doc
import logging
import asyncio

from pymodbus.client.asynchronous.async_io import init_tcp_client
from pymodbus.client.asynchronous import schedulers
from pymodbus.client.asynchronous.thread import EventLoopThread
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


def reactor_factory(
    host="127.0.0.1",
    port=Defaults.Port,
    framer=None,  # pylint: disable=unused-argument
    source_address=None,
    timeout=None,
    **kwargs,
):
    """Create twisted tcp asynchronous client.

    :param host: Host IP address
    :param port: Port
    :param framer: Modbus Framer
    :param source_address: Bind address
    :param timeout: Timeout in seconds
    :param kwargs:
    :return: event_loop_thread and twisted_deferred
    """
    from twisted.internet import (  # pylint: disable=import-outside-toplevel
        reactor,
        protocol,
    )
    from pymodbus.client.asynchronous.twisted import (  # pylint: disable=import-outside-toplevel
        ModbusTcpClientProtocol,
    )

    deferred = protocol.ClientCreator(reactor, ModbusTcpClientProtocol).connectTCP(
        host, port, timeout=timeout, bindAddress=source_address
    )

    callback = kwargs.get("callback")
    errback = kwargs.get("errback")

    if callback:
        deferred.addCallback(callback)

    if errback:
        deferred.addErrback(errback)

    protocol = EventLoopThread(
        "reactor",
        reactor.run,  # pylint: disable=no-member
        reactor.stop,  # pylint: disable=no-member
        installSignalHandlers=0,
    )
    protocol.start()

    return protocol, deferred


def async_io_factory(host="127.0.0.1", port=Defaults.Port, **kwargs):
    """Create asyncio based asynchronous tcp clients.

    :param host: Host IP address
    :param port: Port
    :param kwargs:
    :return: asyncio event loop and tcp client
    """
    try:
        loop = kwargs.pop("loop", None) or asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    proto_cls = kwargs.pop("proto_cls", None)

    if not loop.is_running():
        asyncio.set_event_loop(loop)
        cor = init_tcp_client(proto_cls, loop, host, port, **kwargs)
        client = loop.run_until_complete(asyncio.gather(cor))[0]

    elif loop is asyncio.get_event_loop():
        cor = init_tcp_client(proto_cls, loop, host, port, **kwargs)
        client = asyncio.create_task(cor)
    else:
        cor = init_tcp_client(proto_cls, loop, host, port, **kwargs)
        future = asyncio.run_coroutine_threadsafe(cor, loop=loop)
        client = future.result()

    return loop, client


def get_factory(scheduler):
    """Get protocol factory based on the backend scheduler being used.

    :param scheduler: REACTOR/ASYNC_IO
    :return: new factory
    :raises Exception: Failure
    """
    if scheduler == schedulers.REACTOR:
        return reactor_factory
    if scheduler == schedulers.ASYNC_IO:
        return async_io_factory

    txt = f"Allowed Schedulers: {schedulers.REACTOR}, {schedulers.ASYNC_IO}"
    _logger.warning(txt)
    txt = f'Invalid Scheduler "{scheduler}"'
    raise Exception(txt)
