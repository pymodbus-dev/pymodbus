"""UDP implementation."""
# pylint: disable=missing-type-doc
import asyncio
import logging

from pymodbus.client.asynchronous.async_io import init_udp_client
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


def async_io_factory(host="127.0.0.1", port=Defaults.Port, **kwargs):
    """Create asyncio based asynchronous udp clients.

    :param host: Host IP address
    :param port: Port
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


def get_factory():
    """Get protocol factory.

    :return: new factory
    """
    return async_io_factory
