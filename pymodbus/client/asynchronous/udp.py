"""UDP communication."""
import logging
from pymodbus.constants import Defaults
from pymodbus.client.asynchronous.factory.udp import get_factory

_logger = logging.getLogger(__name__)


class AsyncModbusUDPClient:  # pylint: disable=too-few-public-methods
    """Actual Async UDP Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusUDPClient
    """

    def __new__(
        cls,
        scheduler,
        host="127.0.0.1",
        port=Defaults.Port,
        framer=None,
        source_address=None,
        timeout=None,
        **kwargs
    ):
        """Use scheduler reactor (Twisted), io_loop (Tornado), async_io (asyncio).

        :param scheduler: Backend to use
        :param host: Host IP address
        :param port: Port
        :param framer: Modbus Framer to use
        :param source_address: source address specific to underlying backend
        :param timeout: Time out in seconds
        :param kwargs: Other extra args specific to Backend being used
        :return:
        """
        factory_class = get_factory(scheduler)
        yieldable = factory_class(
            host=host,
            port=port,
            framer=framer,
            source_address=source_address,
            timeout=timeout,
            **kwargs
        )
        return yieldable
