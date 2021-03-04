#!/usr/bin/env python
import contextlib
import sys
import unittest
import pytest
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
if IS_PYTHON3 and PYTHON_VERSION >= (3, 4):
    from unittest.mock import patch, Mock, MagicMock
    import asyncio
    from pymodbus.client.asynchronous.async_io import ReconnectingAsyncioModbusTlsClient
    from pymodbus.client.asynchronous.async_io import AsyncioModbusSerialClient
    from serial_asyncio import SerialTransport
else:
    from mock import patch, Mock, MagicMock
import platform
from distutils.version import LooseVersion

from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient

from pymodbus.client.asynchronous.tornado import AsyncModbusSerialClient as AsyncTornadoModbusSerialClient
from pymodbus.client.asynchronous.tornado import AsyncModbusTCPClient as AsyncTornadoModbusTcpClient
from pymodbus.client.asynchronous.tornado import AsyncModbusUDPClient as AsyncTornadoModbusUdoClient
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusTlsFramer, ModbusRtuFramer, ModbusAsciiFramer, ModbusBinaryFramer
from pymodbus.client.asynchronous.twisted import ModbusSerClientProtocol

import ssl

IS_DARWIN = platform.system().lower() == "darwin"
IS_WINDOWS = platform.system().lower() == "windows"
OSX_SIERRA = LooseVersion("10.12")
if IS_DARWIN:
    IS_HIGH_SIERRA_OR_ABOVE = LooseVersion(platform.mac_ver()[0])
    SERIAL_PORT = '/dev/ttyp0' if not IS_HIGH_SIERRA_OR_ABOVE else '/dev/ptyp0'
else:
    IS_HIGH_SIERRA_OR_ABOVE = False
    if IS_WINDOWS:
        # the use is mocked out
        SERIAL_PORT = ""
    else:
        SERIAL_PORT = "/dev/ptmx"

# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


def mock_asyncio_gather(coro):
    return coro


@contextlib.contextmanager
def maybe_manage(condition, manager):
    if condition:
        with manager as value:
            yield value
    else:
        yield None


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
    # Test TLS Client client
    # -----------------------------------------------------------------------#
    @pytest.mark.skipif(not IS_PYTHON3 or PYTHON_VERSION < (3, 4),
                        reason="requires python3.4 or above")
    def testTlsAsyncioClient(self):
        """
        Test the TLS AsyncIO client
        """
        loop, client = AsyncModbusTLSClient(schedulers.ASYNC_IO)
        assert(isinstance(client, ReconnectingAsyncioModbusTlsClient))
        assert(isinstance(client.framer, ModbusTlsFramer))
        assert(isinstance(client.sslctx, ssl.SSLContext))
        assert(client.port == 802)

        def handle_failure(failure):
            assert(isinstance(failure.exception(), ConnectionException))

        client.stop()
        assert(client.host is None)

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

    @pytest.mark.skipif(
        sys.platform == 'win32' and platform.python_implementation() == 'PyPy',
        reason='Twisted serial requires pywin32 which is not compatible with PyPy',
    )
    @pytest.mark.parametrize("method, framer", [("rtu", ModbusRtuFramer),
                                                ("socket", ModbusSocketFramer),
                                                ("binary", ModbusBinaryFramer),
                                                ("ascii", ModbusAsciiFramer)])
    def testSerialTwistedClient(self, method, framer):
        """ Test the serial twisted client client initialize """
        from serial import Serial
        with patch("serial.Serial") as mock_sp:
            from twisted.internet import reactor
            from twisted.internet.serialport import SerialPort
            with maybe_manage(sys.platform == 'win32', patch.object(SerialPort, "_finishPortSetup")):
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
        from serial import Serial
        with maybe_manage(sys.platform in ('darwin', 'win32'), patch.object(Serial, "open")):
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
        Test Serial asynchronous asyncio client exits on python2
        :return:
        """
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            AsyncModbusSerialClient(schedulers.ASYNC_IO, method="rtu", port=SERIAL_PORT)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    @pytest.mark.skipif(not IS_PYTHON3 or PYTHON_VERSION < (3, 4), reason="requires python3.4 or above")
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    @pytest.mark.parametrize("method, framer", [("rtu", ModbusRtuFramer),
                                        ("socket", ModbusSocketFramer),
                                        ("binary",  ModbusBinaryFramer),
                                        ("ascii", ModbusAsciiFramer)])
    def testSerialAsyncioClient(self,  mock_gather, mock_event_loop, method, framer):
        """
        Test that AsyncModbusSerialClient instantiates AsyncioModbusSerialClient for asyncio scheduler.
        :return:
        """
        loop = asyncio.get_event_loop()
        loop.is_running.side_effect = lambda: False
        loop, client = AsyncModbusSerialClient(schedulers.ASYNC_IO, method=method, port=SERIAL_PORT, loop=loop,
                                               baudrate=19200, parity='E', stopbits=2, bytesize=7)
        assert(isinstance(client, AsyncioModbusSerialClient))
        assert(isinstance(client.framer, framer))
        assert(client.port == SERIAL_PORT)
        assert(client.baudrate == 19200)
        assert(client.parity == 'E')
        assert(client.stopbits == 2)
        assert(client.bytesize == 7)
        client.stop()
        loop.stop()

# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
