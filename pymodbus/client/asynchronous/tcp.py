"""TCP communication."""
import logging
from pymodbus.client.asynchronous.factory.tcp import get_factory
from pymodbus.constants import Defaults

_logger = logging.getLogger(__name__)


class AsyncModbusTCPClient:  # pylint: disable=too-few-public-methods
    """Actual Async Serial Client to be used.

    To use do::
        from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
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
        """Scheduler to use:

            - reactor (Twisted)
            - io_loop (Tornado)
            - async_io (asyncio)
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
