#!/usr/bin/env python
import unittest
from pymodbus.compat import IS_PYTHON3
if IS_PYTHON3:
    from unittest.mock import patch, Mock
else:  # Python 2
    from mock import patch, Mock
from pymodbus.client.asynchronous.tornado import (BaseTornadoClient,
                                                  AsyncModbusSerialClient, AsyncModbusUDPClient, AsyncModbusTCPClient
                                                  )
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.client.asynchronous.twisted import ModbusClientFactory
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer
from pymodbus.bit_read_message import ReadCoilsRequest, ReadCoilsResponse

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#
import platform
from pkg_resources import parse_version

IS_DARWIN = platform.system().lower() == "darwin"
OSX_SIERRA = parse_version("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = OSX_SIERRA < parse_version(platform.mac_ver()[0])
    SERIAL_PORT = '/dev/ptyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ttyp0'
else:
    IS_HIGH_SIERRA_OR_ABOVE = False
    SERIAL_PORT = "/dev/ptmx"


class AsynchronousClientTest(unittest.TestCase):
    """
    This is the unittest for the pymodbus.client.asynchronous module
    """

    # -----------------------------------------------------------------------#
    # Test Client client
    # -----------------------------------------------------------------------#

    def testBaseClientInit(self):
        """ Test the client client initialize """
        client = BaseTornadoClient()
        self.assertTrue(client.port == 502)
        self.assertTrue(client.host == "127.0.0.1")
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)
        self.assertTrue(client.io_loop is None)
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = BaseTornadoClient(framer=framer, ioloop=schedulers.IO_LOOP)
        self.assertEqual(0, len(list(client.transaction)))
        self.assertFalse(client._connected)
        self.assertTrue(client.io_loop == schedulers.IO_LOOP)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testBaseClientOn_receive(self, mock_iostream, mock_ioloop):
        """ Test the BaseTornado client data received """
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        data = b'\x00\x00\x12\x34\x00\x06\xff\x01\x01\x02\x00\x04'

        # setup existing request
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))

        client.on_receive(data)
        self.assertTrue(isinstance(d.result(), ReadCoilsResponse))
        data = b''
        out = []
        d = client._build_response(0x01)
        client.on_receive(data)
        d.add_done_callback(lambda v: out.append(v))
        self.assertFalse(out)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testBaseClientExecute(self, mock_iostream, mock_ioloop):
        """ Test the BaseTornado client execute method """
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()

        request = ReadCoilsRequest(1, 1)
        d = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, client.transaction.getTransaction(tid))

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testBaseClientHandleResponse(self, mock_iostream, mock_ioloop):
        """ Test the BaseTornado client handles responses """
        client = AsyncModbusTCPClient(port=5020)
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)
        client._handle_response(reply)

        # handle existing cases
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))
        client._handle_response(reply)
        self.assertEqual(d.result(), reply)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testBaseClientBuildResponse(self, mock_iostream, mock_ioloop):
        """ Test the BaseTornado client client builds responses """
        client = BaseTornadoClient()
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))
        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True
        d = client._build_response(0x00)
        self.assertEqual(1, len(list(client.transaction)))

    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    def testTcpClientInit(self):
        """ Test the tornado tcp client client initialize """
        client = AsyncModbusTCPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusTCPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testTcpClientConnect(self, mock_iostream, mock_ioloop):
        """ Test the tornado tcp client client connect """
        client = AsyncModbusTCPClient(port=5020)
        self.assertTrue(client.port, 5020)
        self.assertFalse(client._connected)
        client.connect()
        self.assertTrue(client._connected)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testTcpClientDisconnect(self, mock_iostream, mock_ioloop):
        """ Test the tornado tcp client client disconnect """
        client = AsyncModbusTCPClient(port=5020)
        client.connect()

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        self.assertTrue(client._connected)
        client.close()
        self.assertFalse(client._connected)

    # -----------------------------------------------------------------------#
    # Test Serial Client client
    # -----------------------------------------------------------------------#
    def testSerialClientInit(self):
        """ Test the tornado serial client client initialize """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT)
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusRtuFramer))

        framer = object()
        client = AsyncModbusSerialClient(framer=framer)
        self.assertTrue(framer is client.framer)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def testSerialClientConnect(self, mock_serial, mock_seriostream, mock_ioloop):
        """ Test the tornado serial client client connect """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT)
        self.assertTrue(client.port, SERIAL_PORT)
        self.assertFalse(client._connected)
        client.connect()
        self.assertTrue(client._connected)
        client.close()

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def testSerialClientDisconnect(self, mock_serial, mock_seriostream, mock_ioloop):
        """ Test the tornado serial client client disconnect """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT)
        client.connect()
        self.assertTrue(client._connected)

        def handle_failure(failure):
            self.assertTrue(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)
        client.close()
        self.assertFalse(client._connected)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def testSerialClientExecute(self, mock_serial, mock_seriostream, mock_ioloop):
        """ Test the tornado serial client client execute method """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT,
                                         timeout=0)
        client.connect()
        client.stream = Mock()
        client.stream.write = Mock()
        client.stream.connection.read.return_value = b''

        request = ReadCoilsRequest(1, 1)
        d = client.execute(request)
        tid = request.transaction_id
        self.assertEqual(d, client.transaction.getTransaction(tid))

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def testSerialClientHandleResponse(self, mock_serial, mock_seriostream, mock_ioloop):
        """ Test the tornado serial client client handles responses """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT)
        client.connect()
        out = []
        reply = ReadCoilsRequest(1, 1)
        reply.transaction_id = 0x00

        # handle skipped cases
        client._handle_response(None)
        client._handle_response(reply)

        # handle existing cases
        d = client._build_response(0x00)
        d.add_done_callback(lambda v: out.append(v))
        client._handle_response(reply)
        self.assertEqual(d.result(), reply)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.SerialIOStream")
    @patch("pymodbus.client.asynchronous.tornado.Serial")
    def testSerialClientBuildResponse(self, mock_serial, mock_seriostream, mock_ioloop):
        """ Test the tornado serial client client builds responses """
        client = AsyncModbusSerialClient(ioloop=schedulers.IO_LOOP,
                                         framer=ModbusRtuFramer(
                                             ClientDecoder()),
                                         port=SERIAL_PORT)
        self.assertEqual(0, len(list(client.transaction)))

        def handle_failure(failure):
            exc = failure.exception()
            self.assertTrue(isinstance(exc, ConnectionException))
        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)
        self.assertEqual(0, len(list(client.transaction)))

        client._connected = True
        d = client._build_response(0x00)
        self.assertEqual(1, len(list(client.transaction)))

    # -----------------------------------------------------------------------#
    # Test Udp Client client
    # -----------------------------------------------------------------------#

    def testUdpClientInit(self):
        """ Test the udp client client initialize """
        client = AsyncModbusUDPClient()
        self.assertEqual(0, len(list(client.transaction)))
        self.assertTrue(isinstance(client.framer, ModbusSocketFramer))

        framer = object()
        client = AsyncModbusUDPClient(framer=framer)
        self.assertTrue(framer is client.framer)

    # -----------------------------------------------------------------------#
    # Test Client Factories
    # -----------------------------------------------------------------------#

    def testModbusClientFactory(self):
        """ Test the base class for all the clients """
        factory = ModbusClientFactory()
        self.assertTrue(factory is not None)


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    unittest.main()
