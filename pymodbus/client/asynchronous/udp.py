"""UDP communication."""
import logging

from pymodbus.client.asynchronous.async_io import ReconnectingAsyncioModbusUdpClient as udpClient
from pymodbus.client.asynchronous.factory.udp import async_io_factory
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusUDPClient(udpClient):
    """Actual Async UDP Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusUDPClient
    """

    def __new__(
        cls,
        host="127.0.0.1",
        port=Defaults.Port,
        framer=None,
        source_address=None,
        timeout=None,
        **kwargs
    ):
        """Do setup of client.

        :param host: Host IP address
        :param port: Port
        :param framer: Modbus Framer to use
        :param source_address: source address specific to underlying backend
        :param timeout: Time out in seconds
        :param kwargs: Other extra args specific to Backend being used
        :return:
        """
        yieldable = async_io_factory(
            host=host,
            port=port,
            framer=framer,
            source_address=source_address,
            timeout=timeout,
            **kwargs
        )
        return yieldable
