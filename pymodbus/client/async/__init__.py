from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.client.sync import BaseModbusClient

from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer, DictTransactionManager, \
    FifoTransactionManager


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

