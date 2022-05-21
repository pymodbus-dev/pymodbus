#!/usr/bin/env python3
"""Test client async."""
import contextlib
import sys
import ssl
import asyncio
import platform
import unittest
from unittest.mock import patch
from serial import Serial
import pytest

from pymodbus.client.asynchronous.async_io import ReconnectingAsyncioModbusTlsClient
from pymodbus.client.asynchronous.async_io import AsyncioModbusSerialClient
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous.udp import AsyncModbusUDPClient
from pymodbus.client.asynchronous.tornado import (
    AsyncModbusSerialClient as AsyncTornadoModbusSerialClient,
)
from pymodbus.client.asynchronous.tornado import (
    AsyncModbusTCPClient as AsyncTornadoModbusTcpClient,
)
from pymodbus.client.asynchronous.tornado import (
    AsyncModbusUDPClient as AsyncTornadoModbusUdoClient,
)
from pymodbus.client.asynchronous import schedulers
from pymodbus.factory import ClientDecoder
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer, ModbusTlsFramer, ModbusRtuFramer
from pymodbus.transaction import ModbusAsciiFramer, ModbusBinaryFramer
from pymodbus.client.asynchronous.twisted import ModbusSerClientProtocol


# ---------------------------------------------------------------------------#
# Fixture
# ---------------------------------------------------------------------------#


def mock_asyncio_gather(coro):
    """Mock asyncio gather."""
    return coro


@contextlib.contextmanager
def maybe_manage(condition, manager):
    """Maybe manage."""
    if condition:
        with manager as value:
            yield value
    else:
        yield None


class TestAsynchronousClient:
    """Unittest for the pymodbus.client.asynchronous module."""

    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    def test_tcp_twisted_client(self):  # pylint: disable=no-self-use
        """Test the TCP Twisted client."""
        with patch("twisted.internet.reactor"):

            def test_callback(client):  # pylint: disable=unused-argument
                pass

            AsyncModbusTCPClient(
                schedulers.REACTOR,
                framer=ModbusSocketFramer(ClientDecoder()),
                callback=test_callback,
                errback=test_callback,
            )

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_tcp_tornado_client(
        self, mock_iostream, mock_ioloop
    ):  # pylint: disable=no-self-use,unused-argument
        """Test the TCP tornado client client initialize"""
        protocol, future = AsyncModbusTCPClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder())
        )
        client = future.result()
        assert isinstance(client, AsyncTornadoModbusTcpClient)  # nosec
        assert not list(client.transaction)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.port == 502  # nosec
        assert client._connected  # nosec pylint: disable=protected-access
        assert client.stream.connect.call_count == 1  # nosec
        assert client.stream.read_until_close.call_count == 1  # nosec

        def handle_failure(failure):
            assert isinstance(failure.exception(), ConnectionException)  # nosec

        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)

        assert client._connected  # nosec pylint: disable=protected-access
        client.close()
        protocol.stop()
        assert not client._connected  # nosec pylint: disable=protected-access

    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather")
    def test_tcp_asyncio_client(
        self, mock_gather, mock_loop
    ):  # pylint: disable=no-self-use,unused-argument
        """Test the TCP Twisted client."""
        pytest.skip("TBD")

    # -----------------------------------------------------------------------#
    # Test TLS Client client
    # -----------------------------------------------------------------------#

    def test_tls_asyncio_client(self):  # pylint: disable=no-self-use
        """Test the TLS AsyncIO client."""
        _, client = AsyncModbusTLSClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO
        )
        assert isinstance(client, ReconnectingAsyncioModbusTlsClient)  # nosec
        assert isinstance(client.framer, ModbusTlsFramer)  # nosec
        assert isinstance(client.sslctx, ssl.SSLContext)  # nosec
        assert client.port == 802  # nosec

        client.stop()
        assert client.host is None  # nosec

    # -----------------------------------------------------------------------#
    # Test UDP client
    # -----------------------------------------------------------------------#

    @patch("pymodbus.client.asynchronous.tornado.IOLoop")
    @patch("pymodbus.client.asynchronous.tornado.IOStream")
    def test_udp_tornado_client(
        self, mock_iostream, mock_ioloop
    ):  # pylint: disable=no-self-use,unused-argument
        """Test the udp tornado client client initialize"""
        protocol, future = AsyncModbusUDPClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.IO_LOOP, framer=ModbusSocketFramer(ClientDecoder())
        )
        client = future.result()
        assert isinstance(client, AsyncTornadoModbusUdoClient)  # nosec
        assert not list(client.transaction)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.port == 502  # nosec
        assert client._connected  # nosec pylint: disable=protected-access

        def handle_failure(failure):
            assert isinstance(failure.exception(), ConnectionException)  # nosec

        response = client._build_response(0x00)  # pylint: disable=protected-access
        response.add_done_callback(handle_failure)

        assert client._connected  # nosec pylint: disable=protected-access
        client.close()
        protocol.stop()
        assert not client._connected  # nosec pylint: disable=protected-access

    def test_udp_twisted_client(self):  # pylint: disable=no-self-use
        """Test the udp twisted client client initialize"""
        with pytest.raises(NotImplementedError):
            AsyncModbusUDPClient(
                schedulers.REACTOR, framer=ModbusSocketFramer(ClientDecoder())
            )

    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    def test_udp_asyncio_client(
        self, mock_gather, mock_event_loop
    ):  # pylint: disable=no-self-use,unused-argument
        """Test the udp asyncio client"""
        pytest.skip("TBD")

    # -----------------------------------------------------------------------#
    # Test Serial client
    # -----------------------------------------------------------------------#

    @pytest.mark.skipif(
        sys.platform == "win32" and platform.python_implementation() == "PyPy",
        reason="Twisted serial requires pywin32 which is not compatible with PyPy",
    )
    @pytest.mark.parametrize(
        "method, framer",
        [
            ("rtu", ModbusRtuFramer),
            ("socket", ModbusSocketFramer),
            ("binary", ModbusBinaryFramer),
            ("ascii", ModbusAsciiFramer),
        ],
    )
    def test_serial_twisted_client(self, method, framer):  # pylint: disable=no-self-use
        """Test the serial twisted client client initialize"""
        with patch("serial.Serial"):
            from twisted.internet.serialport import (  # pylint: disable=import-outside-toplevel
                SerialPort,
            )

            with maybe_manage(
                sys.platform == "win32", patch.object(SerialPort, "_finishPortSetup")
            ):
                with patch("twisted.internet.reactor"):

                    protocol, client = AsyncModbusSerialClient(  # NOSONAR pylint: disable=unpacking-non-sequence
                        schedulers.REACTOR,
                        method=method,
                        port=pytest.SERIAL_PORT,
                        proto_cls=ModbusSerClientProtocol,
                    )

                    assert isinstance(client, SerialPort)  # nosec
                    assert isinstance(client.protocol, ModbusSerClientProtocol)  # nosec
                    assert not list(client.protocol.transaction)  # nosec
                    assert isinstance(client.protocol.framer, framer)  # nosec
                    assert (
                        client.protocol._connected  # nosec pylint: disable=protected-access
                    )

                    def handle_failure(failure):
                        assert isinstance(
                            failure.exception(), ConnectionException  # nosec
                        )

                    response = client.protocol._buildResponse(  # pylint: disable=protected-access
                        0x00
                    )
                    response.addCallback(handle_failure)

                    assert (
                        client.protocol._connected  # nosec pylint: disable=protected-access
                    )
                    client.protocol.close()
                    protocol.stop()
                    assert (
                        not client.protocol._connected  # nosec pylint: disable=protected-access
                    )

    @pytest.mark.parametrize(
        "method, framer",
        [
            ("rtu", ModbusRtuFramer),
            ("socket", ModbusSocketFramer),
            ("binary", ModbusBinaryFramer),
            ("ascii", ModbusAsciiFramer),
        ],
    )
    def test_serial_tornado_client(self, method, framer):  # pylint: disable=no-self-use
        """Test the serial tornado client client initialize"""
        with maybe_manage(
            sys.platform in {"darwin", "win32"}, patch.object(Serial, "open")
        ):
            protocol, future = AsyncModbusSerialClient(  # NOSONAR pylint: disable=unpacking-non-sequence
                schedulers.IO_LOOP, method=method, port=pytest.SERIAL_PORT
            )
            client = future.result()
            assert isinstance(client, AsyncTornadoModbusSerialClient)  # nosec
            assert not list(client.transaction)  # nosec
            assert isinstance(client.framer, framer)  # nosec
            assert client.port == pytest.SERIAL_PORT  # nosec
            assert client._connected  # nosec pylint: disable=protected-access

            def handle_failure(failure):
                assert isinstance(failure.exception(), ConnectionException)  # nosec

            response = client._build_response(0x00)  # pylint: disable=protected-access
            response.add_done_callback(handle_failure)

            assert client._connected  # nosec pylint: disable=protected-access
            client.close()
            protocol.stop()
            assert not client._connected  # nosec pylint: disable=protected-access

    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    @pytest.mark.parametrize(
        "method, framer",
        [
            ("rtu", ModbusRtuFramer),
            ("socket", ModbusSocketFramer),
            ("binary", ModbusBinaryFramer),
            ("ascii", ModbusAsciiFramer),
        ],
    )
    def test_serial_asyncio_client(  # pylint: disable=no-self-use
        self,
        mock_gather,  # pylint: disable=unused-argument
        mock_event_loop,
        method,
        framer,
    ):  # pylint: disable=unused-argument
        """Test that AsyncModbusSerialClient instantiates AsyncioModbusSerialClient for asyncio scheduler."""
        loop = asyncio.get_event_loop()
        loop.is_running.side_effect = lambda: False
        loop, client = AsyncModbusSerialClient(  # NOSONAR pylint: disable=unpacking-non-sequence
            schedulers.ASYNC_IO,
            method=method,
            port=pytest.SERIAL_PORT,
            loop=loop,
            baudrate=19200,
            parity="E",
            stopbits=2,
            bytesize=7,
        )
        assert isinstance(client, AsyncioModbusSerialClient)  # nosec
        assert isinstance(client.framer, framer)  # nosec
        assert client.port == pytest.SERIAL_PORT  # nosec
        assert client.baudrate == 19200  # nosec
        assert client.parity == "E"  # nosec
        assert client.stopbits == 2  # nosec
        assert client.bytesize == 7  # nosec
        client.stop()
        loop.stop()


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
