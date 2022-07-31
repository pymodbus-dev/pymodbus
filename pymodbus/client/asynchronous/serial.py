"""SERIAL communication."""
import logging

from pymodbus.client.asynchronous.async_io import AsyncioModbusSerialClient as serialClient
from pymodbus.client.asynchronous.factory.serial import async_io_factory
from pymodbus.factory import ClientDecoder

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient(serialClient):
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
        yieldable = async_io_factory(framer=framer, port=port, **kwargs)
        return yieldable
