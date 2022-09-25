#!/usr/bin/env python3
"""Test server sync."""
import socketserver
import ssl
import unittest
from unittest.mock import patch
import pytest

from pymodbus.server.async_io import (
    ModbusSerialServer,
    ModbusTcpServer,
    ModbusTlsServer,
    ModbusUdpServer
)
from pymodbus.server import (
    StartSerialServer,
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
)


class SynchronousServerTest(unittest.TestCase):
    """Unittest for the pymodbus.server.sync module."""

    def xtest_start_tcp_server(self):
        """Test the tcp server starting factory"""
        with patch.object(ModbusTcpServer, "serve_forever"):
            StartTcpServer(bind_and_activate=False)

    def xtest_start_tls_server(self):
        """Test the tls server starting factory"""
        with patch.object(ModbusTlsServer, "serve_forever"):
            with patch.object(ssl.SSLContext, "load_cert_chain"):
                StartTlsServer(bind_and_activate=False)

    def xtest_start_udp_server(self):
        """Test the udp server starting factory"""
        with patch.object(ModbusUdpServer, "serve_forever"):
            with patch.object(socketserver.UDPServer, "server_bind"):
                StartUdpServer()

    @pytest.mark.skip
    def xtest_start_serial_server(self):
        """Test the serial server starting factory"""
        with patch.object(ModbusSerialServer, "serve_forever"):
            StartSerialServer(port=pytest.SERIAL_PORT)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    unittest.main()
