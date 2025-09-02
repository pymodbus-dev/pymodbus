"""Test server asyncio."""
from unittest import mock

import pytest

from pymodbus.datastore import ModbusDeviceContext, ModbusServerContext
from pymodbus.server import (
    ModbusBaseServer,
    ServerAsyncStop,
    ServerStop,
    StartAsyncSerialServer,
    StartAsyncTcpServer,
    StartAsyncTlsServer,
    StartAsyncUdpServer,
    StartSerialServer,
    StartTcpServer,
    StartTlsServer,
    StartUdpServer,
)


SERV_ADDR = ("127.0.0.1", 0)


class TestStartStopServer:
    """Test for the pymodbus.server.startstop module."""

    async def test_ServerAsyncStop(self):
        """Test  ServerAsyncStop."""
        ModbusBaseServer.active_server = None
        with pytest.raises(RuntimeError):
            await ServerAsyncStop()
        ModbusBaseServer.active_server = None
        with pytest.raises(RuntimeError):
            ServerStop()
        ModbusBaseServer.active_server = mock.AsyncMock()
        await ServerAsyncStop()
        ModbusBaseServer.active_server = mock.AsyncMock()
        ServerStop()
        ModbusBaseServer.active_server = None

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    async def test_StartAsyncSerialServer(self, mock_method):
        """Test  StartAsyncSerialServer."""
        mock_method.return_value=True
        await StartAsyncSerialServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True),
            port="/dev/tty01",
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    async def test_StartAsyncTcpServer(self, mock_method):
        """Test  StartAsyncTcpServer."""
        mock_method.return_value=True
        await StartAsyncTcpServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    async def test_StartAsyncTlsServer(self, mock_method):
        """Test  StartAsyncTlsServer."""
        mock_method.return_value=True
        await StartAsyncTlsServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    async def test_StartAsyncUdpServer(self, mock_method):
        """Test  StartAsyncUdpServer."""
        mock_method.return_value=True
        await StartAsyncUdpServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )

    def test_ServerStop(self):
        """Test  ServerStop."""

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    def test_StartSerialServer(self, mock_method):
        """Test  StartSerialServer."""
        mock_method.return_value=True
        StartSerialServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True),
            port="/dev/tty01",
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    def test_StartTcpServer(self, mock_method):
        """Test  StartTcpServer."""
        mock_method.return_value=True
        StartTcpServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    def test_StartTlsServer(self, mock_method):
        """Test  StartTlsServer."""
        mock_method.return_value=True
        StartTlsServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )

    @mock.patch('pymodbus.server.ModbusBaseServer.serve_forever')
    def test_StartUdpServer(self, mock_method):
        """Test  StartUdpServer."""
        mock_method.return_value=True
        StartUdpServer(
            ModbusServerContext(devices=ModbusDeviceContext(), single=True)
        )
