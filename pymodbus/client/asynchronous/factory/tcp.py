"""Factory to create asynchronous tcp clients based on asyncio."""
# pylint: disable=missing-type-doc
import asyncio
import logging

from pymodbus.client.asynchronous.async_io import init_tcp_client
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


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


def get_factory():
    """Get protocol factory.

    :return: new factory
    """
    return async_io_factory
