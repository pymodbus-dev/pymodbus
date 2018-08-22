#!/usr/bin/env python
import unittest
import pytest
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
if IS_PYTHON3 and PYTHON_VERSION >= (3, 4):
    from unittest.mock import patch, Mock, MagicMock
    import asyncio
    from pymodbus.client.asynchronous.asyncio import AsyncioModbusSerialClient
    from serial_asyncio import SerialTransport
else:
    from mock import patch, Mock, MagicMock
import platform
from distutils.version import LooseVersion

from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient

from pymodbus.client.asynchronous.tornado import AsyncModbusSerialClient as AsyncTornadoModbusSerialClient
from pymodbus.client.asynchronous.tornado import AsyncModbusTCPClient as AsyncTornadoModbusTcpClient
from pymodbus.client.asynchronous.tornado import AsyncModbusUDPClient as AsyncTornadoModbusUdoClient
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusRtuFramer, ModbusAsciiFramer, ModbusBinaryFramer
from pymodbus.client.asynchronous.twisted import ModbusSerClientProtocol

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


def mock_create_serial_connection(a, b, port):
    ser = MagicMock()
    ser.port = port
    protocol = b()
    transport = SerialTransport(a, protocol, ser)
    protocol.transport = transport
    return transport, protocol


def mock_asyncio_gather(coro):
    return coro


def mock_asyncio_run_untill_complete(val):
    transport, protocol = val
    protocol._connected = True
    return ([transport, protocol], )


class TestAsynchronousClient(object):
    """
    This is the unittest for the pymodbus.client.asynchronous module
    """

    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    def testTcpTwistedClient(self):
        """
        Test the TCP Twisted client
        :return:
        """
        from twisted.internet import reactor
        with patch("twisted.internet.reactor") as mock_reactor:
            def test_callback(client):
                pass

            def test_errback(client):
                pass
            AsyncModbusTCPClient(schedulers.REACTOR,
                                 framer=ModbusSocketFramer(ClientDecoder()),
                                 callback=test_callback,
                                 errback=test_errback)

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testTcpTornadoClient(self, mock_iostream, mock_ioloop):
        """ Test the TCP tornado client client initialize """
        protocol, future = AsyncModbusTCPClient(schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder()))
        client = future.result()
        assert(isinstance(client, AsyncTornadoModbusTcpClient))
        assert(0 == len(list(client.transaction)))
        assert(isinstance(client.framer, ModbusSocketFramer))
        assert(client.port == 502)
        assert client._connected
        assert(client.stream.connect.call_count == 1)
        assert(client.stream.read_until_close.call_count == 1)

        def handle_failure(failure):
            assert(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        assert(client._connected)
        client.close()
        protocol.stop()
        assert(not client._connected)

    @pytest.mark.skipif(not IS_PYTHON3 or PYTHON_VERSION < (3, 4),
                        reason="requires python3.4 or above")
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather")
    def testTcpAsyncioClient(self, mock_gather, mock_loop):
        """
        Test the TCP Twisted client
        :return:
        """
        pytest.skip("TBD")

    # -----------------------------------------------------------------------#
    # Test UDP client
    # -----------------------------------------------------------------------#

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def testUdpTornadoClient(self, mock_iostream, mock_ioloop):
        """ Test the udp tornado client client initialize """
        protocol, future = AsyncModbusUDPClient(schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder()))
        client = future.result()
        assert(isinstance(client, AsyncTornadoModbusUdoClient))
        assert(0 == len(list(client.transaction)))
        assert(isinstance(client.framer, ModbusSocketFramer))
        assert(client.port == 502)
        assert(client._connected)

        def handle_failure(failure):
            assert(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        assert(client._connected)
        client.close()
        protocol.stop()
        assert(not client._connected)

    def testUdpTwistedClient(self):
        """ Test the udp twisted client client initialize """
        with pytest.raises(NotImplementedError):
            AsyncModbusUDPClient(schedulers.REACTOR,
                                 framer=ModbusSocketFramer(ClientDecoder()))

    @pytest.mark.skipif(not IS_PYTHON3 or PYTHON_VERSION < (3, 4),
                        reason="requires python3.4 or above")
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    def testUdpAsycioClient(self, mock_gather, mock_event_loop):
        """Test the udp asyncio client"""
        pytest.skip("TBD")
        pass

    # -----------------------------------------------------------------------#
    # Test Serial client
    # -----------------------------------------------------------------------#

    @pytest.mark.parametrize("method, framer", [("rtu", ModbusRtuFramer),
                                                ("socket", ModbusSocketFramer),
                                                ("binary", ModbusBinaryFramer),
                                                ("ascii", ModbusAsciiFramer)])
    def testSerialTwistedClient(self, method, framer):
        """ Test the serial tornado client client initialize """
        from serial import Serial
        with patch("serial.Serial") as mock_sp:
            from twisted.internet import reactor
            from twisted.internet.serialport import SerialPort

            with patch('twisted.internet.reactor') as mock_reactor:

                protocol, client = AsyncModbusSerialClient(schedulers.REACTOR,
                                                           method=method,
                                                           port=SERIAL_PORT,
                                                           proto_cls=ModbusSerClientProtocol)

                assert (isinstance(client, SerialPort))
                assert (isinstance(client.protocol, ModbusSerClientProtocol))
                assert (0 == len(list(client.protocol.transaction)))
                assert (isinstance(client.protocol.framer, framer))
                assert (client.protocol._connected)

                def handle_failure(failure):
                    assert (isinstance(failure.exception(), ConnectionException))

                d = client.protocol._buildResponse(0x00)
                d.addCallback(handle_failure)

                assert (client.protocol._connected)
                client.protocol.close()
                protocol.stop()
                assert (not client.protocol._connected)

    @pytest.mark.parametrize("method, framer", [("rtu", ModbusRtuFramer),
                                        ("socket", ModbusSocketFramer),
                                        ("binary",  ModbusBinaryFramer),
                                        ("ascii", ModbusAsciiFramer)])
    def testSerialTornadoClient(self, method, framer):
        """ Test the serial tornado client client initialize """
        protocol, future = AsyncModbusSerialClient(schedulers.IO_LOOP, method=method, port=SERIAL_PORT)
        client = future.result()
        assert(isinstance(client, AsyncTornadoModbusSerialClient))
        assert(0 == len(list(client.transaction)))
        assert(isinstance(client.framer, framer))
        assert(client.port == SERIAL_PORT)
        assert(client._connected)

        def handle_failure(failure):
            assert(isinstance(failure.exception(), ConnectionException))

        d = client._build_response(0x00)
        d.add_done_callback(handle_failure)

        assert(client._connected)
        client.close()
        protocol.stop()
        assert(not client._connected)

    @pytest.mark.skipif(IS_PYTHON3 , reason="requires python2.7")
    def testSerialAsyncioClientPython2(self):
        """
        Test Serial async asyncio client exits on python2
        :return:
        """
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            AsyncModbusSerialClient(schedulers.ASYNC_IO, method="rtu", port=SERIAL_PORT)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    @pytest.mark.skipif(not IS_PYTHON3 or PYTHON_VERSION < (3, 4), reason="requires python3.4 or above")
    @patch("serial_asyncio.create_serial_connection", side_effect=mock_create_serial_connection)
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    @pytest.mark.parametrize("method, framer", [("rtu", ModbusRtuFramer),
                                        ("socket", ModbusSocketFramer),
                                        ("binary",  ModbusBinaryFramer),
                                        ("ascii", ModbusAsciiFramer)])
    def testSerialAsyncioClient(self,  mock_gather, mock_event_loop, mock_serial_connection, method, framer):
        """
        Test Serial async asyncio client exits on python2
        :return:
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete.side_effect = mock_asyncio_run_untill_complete
        loop, client = AsyncModbusSerialClient(schedulers.ASYNC_IO, method=method, port=SERIAL_PORT, loop=loop)
        assert(isinstance(client, AsyncioModbusSerialClient))
        assert(len(list(client.protocol.transaction)) == 0)
        assert(isinstance(client.framer, framer))
        assert(client.protocol._connected)

        d = client.protocol._buildResponse(0x00)

        def handle_failure(failure):
            assert(isinstance(failure.exception(), ConnectionException))

        d.add_done_callback(handle_failure)
        assert(client.protocol._connected)
        client.protocol.close()
        assert(not client.protocol._connected)
        pass


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
