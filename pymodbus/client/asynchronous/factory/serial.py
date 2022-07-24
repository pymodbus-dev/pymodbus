"""Factory to create asynchronous serial clients based on asyncio."""
# pylint: disable=missing-type-doc
import asyncio
import logging

from pymodbus.client.asynchronous.async_io import (
    AsyncioModbusSerialClient,
    ModbusClientProtocol,
)

_logger = logging.getLogger(__name__)


def async_io_factory(port=None, framer=None, **kwargs):
    """Create asyncio based asynchronous serial clients.

    :param port:  Serial port
    :param framer: Modbus Framer
    :param kwargs: Serial port options
    :return: asyncio event loop and serial client
    """
    try:
        loop = kwargs.pop("loop", None) or asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    proto_cls = kwargs.get("proto_cls") or ModbusClientProtocol

    client = AsyncioModbusSerialClient(port, proto_cls, framer, loop, **kwargs)
    coro = client.connect
    if not loop.is_running():
        loop.run_until_complete(coro())
    else:  # loop is not asyncio.get_event_loop():
        future = asyncio.run_coroutine_threadsafe(coro(), loop=loop)
        future.result()

    return loop, client


def get_factory():
    """Get protocol factory.

    :return: new factory
    """
    return async_io_factory
