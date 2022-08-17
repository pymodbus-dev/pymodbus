#!/usr/bin/env python3
"""Test client async."""
import asyncio
import contextlib
import ssl
import unittest

import pytest

from pymodbus.client import (
    AsyncModbusUdpClient,
    AsyncModbusTlsClient,
    AsyncModbusSerialClient,
    AsyncModbusTcpClient,
)
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
    """Unittest for the pymodbus.client async module."""

    # -----------------------------------------------------------------------#
    # Test TCP Client client
    # -----------------------------------------------------------------------#
    async def test_tcp_no_asyncio_client(self):
        """Test the TCP client."""
        client = AsyncModbusTcpClient("127.0.0.1")
        assert isinstance(client, AsyncModbusTcpClient)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.params.port == 502  # nosec

        await client.aClose()
        assert client.params.host is None  # nosec

    async def test_tcp_asyncio_client(self):
        """Test the TCP client."""
        client = AsyncModbusTcpClient("127.0.0.1")
        assert isinstance(client, AsyncModbusTcpClient)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.params.port == 502  # nosec

        await client.aClose()
        assert client.params.host is None  # nosec

    # -----------------------------------------------------------------------#
    # Test TLS Client client
    # -----------------------------------------------------------------------#

    async def test_tls_no_asyncio_client(self):
        """Test the TLS AsyncIO client."""
        client = AsyncModbusTlsClient("127.0.0.1")
        assert isinstance(client, AsyncModbusTlsClient)  # nosec
        assert isinstance(client.framer, ModbusTlsFramer)  # nosec
        assert isinstance(client.sslctx, ssl.SSLContext)  # nosec
        assert client.params.port == 802  # nosec

        await client.aClose()
        assert client.params.host is None  # nosec

    async def test_tls_asyncio_client(self):
        """Test the TLS AsyncIO client."""
        client = AsyncModbusTlsClient("127.0.0.1")
        assert isinstance(client, AsyncModbusTlsClient)  # nosec
        assert isinstance(client.framer, ModbusTlsFramer)  # nosec
        assert isinstance(client.sslctx, ssl.SSLContext)  # nosec
        assert client.params.port == 802  # nosec

        await client.aClose()
        assert client.params.host is None  # nosec

    # -----------------------------------------------------------------------#
    # Test UDP client
    # -----------------------------------------------------------------------#
    async def test_udp_no_asyncio_client(self):
        """Test the udp asyncio client"""
        client = AsyncModbusUdpClient("127.0.0.1")
        assert isinstance(client, AsyncModbusUdpClient)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.params.port == 502  # nosec

        await client.aClose()
        # TBD assert client.params.host is None  # nosec

    async def test_udp_asyncio_client(self):
        """Test the udp asyncio client"""
        client = AsyncModbusUdpClient("127.0.0.1")
        assert isinstance(client, AsyncModbusUdpClient)  # nosec
        assert isinstance(client.framer, ModbusSocketFramer)  # nosec
        assert client.params.port == 502  # nosec

        await client.aClose()
        # TBD assert client.params.host is None  # nosec

    # -----------------------------------------------------------------------#
    # Test Serial client
    # -----------------------------------------------------------------------#

    async def test_serial_no_asyncio_client(self):
        """Test that AsyncModbusSerialClient instantiates AsyncModbusSerialClient for asyncio scheduler."""
        client = AsyncModbusSerialClient(port="not here", framer=ModbusRtuFramer)
        assert isinstance(client, AsyncModbusSerialClient)  # nosec
        assert isinstance(client.framer, ModbusRtuFramer)  # nosec
        await client.aClose()

    @pytest.mark.parametrize(
        "framer",
        [
            ModbusRtuFramer,
            ModbusSocketFramer,
            ModbusBinaryFramer,
            ModbusAsciiFramer,
        ],
    )
    async def test_serial_asyncio_client(
        self,
        framer,
    ):
        """Test that AsyncModbusSerialClient instantiates AsyncModbusSerialClient for asyncio scheduler."""
        client = AsyncModbusSerialClient(
            framer=framer,
            port=pytest.SERIAL_PORT,
            baudrate=19200,
            parity="E",
            stopbits=2,
            bytesize=7,
            timeout=1,
        )
        assert isinstance(client, AsyncModbusSerialClient)  # nosec
        assert isinstance(client.framer, framer)  # nosec
        assert client.params.port == pytest.SERIAL_PORT  # nosec
        assert client.baudrate == 19200  # nosec
        assert client.parity == "E"  # nosec
        assert client.stopbits == 2  # nosec
        assert client.bytesize == 7  # nosec
        asyncio.wait_for(client.aConnect(), timeout=1)
        await client.aClose()


# ---------------------------------------------------------------------------#
# Main
# ---------------------------------------------------------------------------#


if __name__ == "__main__":
    unittest.main()
