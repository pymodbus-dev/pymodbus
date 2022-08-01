#!/usr/bin/env python3
"""Test client async."""
import asyncio
import contextlib
import ssl
import unittest
from unittest.mock import patch

import pytest

from pymodbus.client.asynchronous.async_io import (
    AsyncioModbusSerialClient,
    ReconnectingAsyncioModbusTlsClient,
)
from pymodbus.client.asynchronous.serial import AsyncModbusSerialClient
from pymodbus.client.asynchronous.tls import AsyncModbusTLSClient
from pymodbus.transaction import (
    ModbusAsciiFramer,
    ModbusBinaryFramer,
    ModbusRtuFramer,
    ModbusSocketFramer,
    ModbusTlsFramer,
)

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
    # Test TLS Client client
    # -----------------------------------------------------------------------#
    def test_tls_asyncio_client(self):
        """Test the TLS AsyncIO client."""
        _, client = AsyncModbusTLSClient()  # pylint: disable=unpacking-non-sequence
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
    ):  # pylint: disable=unused-argument
        """Test the udp asyncio client"""
        pytest.skip("TBD")

    # -----------------------------------------------------------------------#
    # Test Serial client
    # -----------------------------------------------------------------------#
    @patch("asyncio.get_event_loop")
    @patch("asyncio.gather", side_effect=mock_asyncio_gather)
    @pytest.mark.parametrize(
        "framer",
        [
            ModbusRtuFramer,
            ModbusSocketFramer,
            ModbusBinaryFramer,
            ModbusAsciiFramer,
        ],
    )
    @pytest.mark.asyncio
    async def test_serial_asyncio_client(
        self,
        mock_gather,  # pylint: disable=unused-argument
        mock_event_loop,
        framer,
    ):  # pylint: disable=unused-argument
        """Test that AsyncModbusSerialClient instantiates AsyncioModbusSerialClient for asyncio scheduler."""
        loop = asyncio.get_event_loop()
        loop.is_running.side_effect = lambda: False
        (  # pylint: disable=unpacking-non-sequence
            loop,
            client,
        ) = AsyncModbusSerialClient(
            framer=framer,
            port=pytest.SERIAL_PORT,
            loop=loop,
            baudrate=19200,
            parity="E",
            stopbits=2,
            bytesize=7,
            timeout=1,
        )
        assert isinstance(client, AsyncioModbusSerialClient)  # nosec
        assert isinstance(client.framer, framer)  # nosec
        assert client.port == pytest.SERIAL_PORT  # nosec
        assert client.baudrate == 19200  # nosec
        assert client.parity == "E"  # nosec
        assert client.stopbits == 2  # nosec
        assert client.bytesize == 7  # nosec
        asyncio.wait_for(client.connect(), timeout=1)
        client.stop()
        loop.stop()


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
