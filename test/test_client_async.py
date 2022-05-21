#!/usr/bin/env python3
"""Test client async."""
import contextlib
import ssl
import asyncio
import unittest
from unittest.mock import patch
import pytest

from pymodbus.client.asynchronous.async_io import ReconnectingAsyncioModbusTlsClient
from pymodbus.client.asynchronous.async_io import AsyncioModbusSerialClient
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.client.asynchronous import schedulers
from pymodbus.transaction import ModbusSocketFramer, ModbusTlsFramer, ModbusRtuFramer
from pymodbus.transaction import ModbusAsciiFramer, ModbusBinaryFramer


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
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather")
    def test_tcp_asyncio_client(
        self, mock_gather, mock_loop
    ):  # pylint: disable=no-self-use,unused-argument
        """Test the TCP client."""
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
