#!/usr/bin/env python
import unittest
from pymodbus.compat import IS_PYTHON3
if IS_PYTHON3:
    from unittest.mock import patch, Mock, MagicMock
else: # Python 2
    from mock import patch, Mock, MagicMock
import platform
from distutils.version import LooseVersion
import serial
import sys
from pymodbus.client.async.serial import  AsyncModbusSerialClient
from pymodbus.client.async.tcp import AsyncModbusTCPClient
from pymodbus.client.async.udp import AsyncModbusUDPClient

from pymodbus.client.async.tornado import AsyncModbusSerialClient as AsyncTornadoModbusSerialClient
from pymodbus.client.async.tornado import AsyncModbusTCPClient as AsyncTornadoModbusTcpClient
from pymodbus.client.async.tornado import AsyncModbusUDPClient as AsyncTornadoModbusUdoClient
from pymodbus.client.async import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer

IS_DARWIN = platform.system().lower() == "darwin"
OSX_SIERRA = LooseVersion("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = LooseVersion(platform.mac_ver()[0])
    SERIAL_PORT = '/dev/ttyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ptyp0'
else:
    IS_HIGH_SIERRA_OR_ABOVE = False
    SERIAL_PORT = "/dev/ptmx"

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


class AsynchronousClientTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus.client.async module
    """
    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    @patch("pymodbus.client.async.tornado.IOLoop")
    @patch("pymodbus.client.async.tornado.IOStream")
    def testTcpTornadoClient(self, mock_iostream, mock_ioloop):
        """ Test the TCP tornado client client initialize """
        protocol, future = AsyncModbusTCPClient(schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder()))
        client = future.result()
        self.assertTrue(isinstance(client, AsyncTornadoModbusTcpClient))
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))
        self.assertTrue(client.port == 502)
        self.assertTrue(client._connected)
        self.assertTrue(client.stream.connect.call_count, 1)
        self.assertTrue(client.stream.read_until_close.call_count, 1)

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        protocol.stop()
        self.assertFalse(client._connected)

    def testUdpTornadoClient(self):
        """ Test the udp tornado client client initialize """
        protocol, future = AsyncModbusUDPClient(schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder()))
        client = future.result()
        self.assertTrue(isinstance(client, AsyncTornadoModbusUdoClient))
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))
        self.assertTrue(client.port == 502)
        self.assertTrue(client._connected)

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        protocol.stop()
        self.assertFalse(client._connected)

    def testUdpTwistedClient(self):
        """ Test the udp twisted client client initialize """
        with self.assertRaises(NotImplementedError):
            AsyncModbusUDPClient(schedulers.REACTOR,
                                 framer=ModbusSocketFramer(ClientDecoder()))

    def testSerialTornadoClient(self):
        """ Test the serial tornado client client initialize """
        protocol, future = AsyncModbusSerialClient(schedulers.IO_LOOP, port=SERIAL_PORT,framer=ModbusRtuFramer(ClientDecoder()))
        client = future.result()
        self.assertTrue(isinstance(client, AsyncTornadoModbusSerialClient))
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusRtuFramer))
        self.assertTrue(client.port == SERIAL_PORT)
        self.assertTrue(client._connected)

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        protocol.stop()
        self.assertFalse(client._connected)

# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
