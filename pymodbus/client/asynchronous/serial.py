"""SERIAL communication."""
import asyncio
import logging

from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.async_io import (
    AsyncioModbusSerialClient,
    ModbusClientProtocol,
)

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient(AsyncioModbusSerialClient):
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
    """

    def __new__(cls, framer, port, **kwargs):
        """Do setup of client.

        :param framer: Modbus Framer
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout between serial requests (default 3s)
        :param kwargs:
        :return:
        """
        framer = framer(ClientDecoder())
        try:
            loop = kwargs.pop("loop", None) or asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        proto_cls = kwargs.get("proto_cls") or ModbusClientProtocol

        client = AsyncioModbusSerialClient(port, proto_cls, framer, **kwargs)
        coro = client.connect
        if not loop.is_running():
            loop.run_until_complete(coro())
        else:  # loop is not asyncio.get_event_loop():
            future = asyncio.run_coroutine_threadsafe(coro(), loop=loop)
            future.result()
        return client
