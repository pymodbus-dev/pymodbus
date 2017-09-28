from __future__ import unicode_literals
from __future__ import absolute_import

import logging

from pymodbus.factory import ClientDecoder
from pymodbus.transaction import ModbusSocketFramer, DictTransactionManager, \
    FifoTransactionManager


LOGGER = logging.getLogger(__name__)


class BaseAsyncModbusClient(object):
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
        self.framer = framer or ModbusSocketFramer(ClientDecoder())

        if isinstance(self.framer, ModbusSocketFramer):
            self.transaction = DictTransactionManager(self, **kwargs)
        else:
            self.transaction = FifoTransactionManager(self, **kwargs)


