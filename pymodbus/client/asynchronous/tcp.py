"""TCP communication."""
import logging

from pymodbus.client.asynchronous.async_io import (
    init_tcp_client,
    ReconnectingAsyncioModbusTcpClient,
)
from pymodbus.constants import Defaults
from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer

_logger = logging.getLogger(__name__)


class AsyncModbusTCPClient(ReconnectingAsyncioModbusTcpClient):
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
    """

    def __new__(
        cls,
        host="127.0.0.1",
        port=Defaults.Port,
        framer=None,
        **kwargs
    ):
        """Scheduler to use async_io (asyncio)

        :param host: Host IP address
        :param port: Port
        :param framer: Modbus Framer to use
        :param source_address: source address specific to underlying backend
        :param timeout: Time out in seconds
        :param kwargs: Other extra args specific to Backend being used
        :return:
        """
        framer = framer or ModbusSocketFramer(ClientDecoder())
        proto_cls = kwargs.pop("proto_cls", None)

        return init_tcp_client(proto_cls, host, port, framer=framer, **kwargs)
