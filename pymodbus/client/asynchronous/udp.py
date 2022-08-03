"""UDP communication."""
import logging

from pymodbus.client.asynchronous.async_io import (
    ReconnectingAsyncioModbusUdpClient,
)
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer

_logger = logging.getLogger(__name__)


class AsyncModbusUDPClient(ReconnectingAsyncioModbusUdpClient):
    """Actual Async UDP Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusUDPClient
    """

    def __new__(
        cls,
        host,
        **kwargs
    ):
        """Do setup of client.

        :param host: Host IP address
        :param port: Port
        :param framer: Modbus Framer to use
        :param source_address: source address specific to underlying backend
        :param timeout: Time out in seconds
        :param protocol_class: Protocol used to talk to modbus device.
        :param modbus_decoder: Message decoder.
        :param kwargs: Other extra args specific to Backend being used
        :return: client object
        """
        decoder = kwargs.pop("modbus_decoder", ClientDecoder)
        raw_framer = kwargs.pop("framer", ModbusSocketFramer)
        framer = raw_framer(decoder())
        client = ReconnectingAsyncioModbusUdpClient(host, framer=framer, **kwargs)
        return client
