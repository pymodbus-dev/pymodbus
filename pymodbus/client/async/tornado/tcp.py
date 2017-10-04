from __future__ import unicode_literals

import socket

import logging

from pymodbus.client.async.tornado import BaseTornadoClient
from pymodbus.client.common import ModbusClientMixin


LOGGER = logging.getLogger(__name__)


class AsyncModbusTCPClient(BaseTornadoClient, ModbusClientMixin):
    def get_socket(self):
        return socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
