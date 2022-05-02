"""SERIAL communication."""
import logging
from pymodbus.client.asynchronous.factory.serial import get_factory
from pymodbus.transaction import (
    ModbusRtuFramer,
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusSocketFramer,
)
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ParameterException

_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient:  # pylint: disable=too-few-public-methods
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
    """

    @classmethod
    def _framer(cls, method):
        """Return the requested framer

        :method: The serial framer to instantiate
        :returns: The requested serial framer
        """
        method = method.lower()
        if method == "ascii":
            return ModbusAsciiFramer(ClientDecoder())
        if method == "rtu":
            return ModbusRtuFramer(ClientDecoder())
        if method == "binary":
            return ModbusBinaryFramer(ClientDecoder())
        if method == "socket":
            return ModbusSocketFramer(ClientDecoder())

        raise ParameterException("Invalid framer method requested")

    def __new__(cls, scheduler, method, port, **kwargs):
        """Use scheduler reactor (Twisted), io_loop (Tornado), async_io (asyncio).

        The methods to connect are::
          - ascii
          - rtu
          - binary
        :param scheduler: Backend to use
        :param method: The method to use for connection
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout between serial requests (default 3s)
        :param scheduler:
        :param method:
        :param port:
        :param kwargs:
        :return:
        """
        factory_class = get_factory(scheduler)
        framer = cls._framer(method)
        yieldable = factory_class(framer=framer, port=port, **kwargs)
        return yieldable
