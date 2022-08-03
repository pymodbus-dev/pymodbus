"""SERIAL communication."""
import logging

from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.async_io import AsyncioModbusSerialClient
from pymodbus.transaction import ModbusRtuFramer


_logger = logging.getLogger(__name__)


class AsyncModbusSerialClient(AsyncioModbusSerialClient):
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
    """

    def __new__(cls, port, **kwargs):
        """Do setup of client.

        :param framer: Modbus Framer
        :param port: The serial port to attach to
        :param stopbits: The number of stop bits to use
        :param bytesize: The bytesize of the serial messages
        :param parity: Which kind of parity to use
        :param baudrate: The baud rate to use for the serial device
        :param timeout: The timeout between serial requests (default 3s)
        :param protocol_class: Protocol used to talk to modbus device.
        :param modbus_decoder: Message decoder.
        :param kwargs:
        :return:
        """
        decoder = kwargs.pop("modbus_decoder", ClientDecoder)
        raw_framer = kwargs.pop("framer", ModbusRtuFramer)
        framer = raw_framer(decoder())
        client = AsyncioModbusSerialClient(port, framer=framer, **kwargs)
        return client
