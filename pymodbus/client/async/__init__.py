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
    def __init__(self, host="127.0.0.1", port=Defaults.Port, framer=None,
                 source_address=None, timeout=None, **kwargs):
        super(AsyncModbusClientMixin, self).__init__(framer=framer, **kwargs)
        self.host = host
        self.port = port
        self.source_address = source_address or ("", 0)
        self.timeout = timeout if timeout is not None else Defaults.Timeout


class AsyncModbusSerialClientMixin(BaseAsyncModbusClient):
    def __init__(self, framer=None, port=None, **kwargs):
        super(AsyncModbusSerialClientMixin, self).__init__(framer=framer)
        self.port = port
        self.serial_settings = kwargs

