"""UDP communication."""
import asyncio
import logging

from pymodbus.client.asynchronous.async_io import (
    init_udp_client,
    ReconnectingAsyncioModbusUdpClient,
)
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusUDPClient(ReconnectingAsyncioModbusUdpClient):
    """Actual Async UDP Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusUDPClient
    """

    def __new__(
        cls,
        host="127.0.0.1",
        port=Defaults.Port,
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
        try:
            loop = kwargs.pop("loop", None) or asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        proto_cls = kwargs.pop("proto_cls", None)
        cor = init_udp_client(proto_cls, host, port, **kwargs)
        if not loop.is_running():
            cor = init_udp_client(proto_cls, host, port)
            client = loop.run_until_complete(asyncio.gather(cor))[0]
        elif loop is asyncio.get_event_loop():
            return init_udp_client(proto_cls, host, port)

        cor = init_udp_client(proto_cls, host, port)
        client = asyncio.run_coroutine_threadsafe(cor, loop=loop)
        client = client.result()
        return client
