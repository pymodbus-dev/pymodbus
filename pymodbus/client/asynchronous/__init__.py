"""
Async Modbus Client implementation based on Twisted, tornado and asyncio
------------------------------------------------------------------------

Example run::

    from pymodbus.client.asynchronous import schedulers

    # Import The clients

    from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as Client
    from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient as Client
    from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient as Client

    # For tornado based asynchronous client use
    event_loop, future = Client(schedulers.IO_LOOP, port=5020)

    # For twisted based asynchronous client use
    event_loop, future = Client(schedulers.REACTOR, port=5020)

    # For asyncio based asynchronous client use
    event_loop, client = Client(schedulers.ASYNC_IO, port=5020)

    # Here event_loop is a thread which would control the backend and future is
    # a Future/deffered object which would be used to
    # add call backs to run asynchronously.

    # The Actual client could be accessed with future.result() with Tornado
    # and future.result when using twisted

    # For asyncio the actual client is returned and event loop is asyncio loop

"""
from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.sync import BaseModbusClient

from pymodbus.constants import Defaults

from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer


LOGGER = logging.getLogger(__name__)


class BaseAsyncModbusClient(BaseModbusClient):
    """
    This represents the base ModbusAsyncClient.
    """

    def __init__(self, framer=None, **kwargs):
        """ Initializes the framer module

        :param framer: The framer to use for the protocol. Default:
        ModbusSocketFramer
        :type framer: pymodbus.transaction.ModbusSocketFramer
        """
        self._connected = False

        super(BaseAsyncModbusClient, self).__init__(
            framer or ModbusSocketFramer(ClientDecoder()), **kwargs
        )


class AsyncModbusClientMixin(BaseAsyncModbusClient):
    """
    Async Modbus client mixing for UDP and TCP clients
    """
    def __init__(self, host="127.0.0.1", port=Defaults.Port, framer=None,
                 source_address=None, timeout=None, **kwargs):
        """
        Initializes a Modbus TCP/UDP asynchronous client
        :param host: Host IP address
        :param port: Port
        :param framer: Framer to use
        :param source_address: Specific to underlying client being used
        :param timeout: Timeout in seconds
        :param kwargs: Extra arguments
        """
        super(AsyncModbusClientMixin, self).__init__(framer=framer, **kwargs)
        self.host = host
        self.port = port
        self.source_address = source_address or ("", 0)
        self.timeout = timeout if timeout is not None else Defaults.Timeout


class AsyncModbusSerialClientMixin(BaseAsyncModbusClient):
    """
    Async Modbus Serial Client Mixing
    """
    def __init__(self, framer=None, port=None, **kwargs):
        """
        Initializes a Async Modbus Serial Client
        :param framer:  Modbus Framer
        :param port: Serial port to use
        :param kwargs: Extra arguments if any
        """
        super(AsyncModbusSerialClientMixin, self).__init__(framer=framer)
        self.port = port
        self.serial_settings = kwargs

