"""SERIAL communication."""
import logging

from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.async_io import (
    AsyncioModbusSerialClient,
    ModbusClientProtocol,
)

_logger = logging.getLogger(__name__)


async def init_serial_client(port, proto_cls, framer, **kwargs):
    """Initialize UDP client with helper function."""
    client = AsyncioModbusSerialClient(
        port, proto_cls, framer=framer, **kwargs
    )
    await client.connect()
    return client


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
        proto_cls = kwargs.get("proto_cls") or ModbusClientProtocol

        client = init_serial_client(port, proto_cls, framer=framer, **kwargs)
        return client
