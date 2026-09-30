"""Test transport."""

import asyncio
import os
import sys
from unittest import mock

import pytest

from pymodbus.transport.serialtransport import SerialInterface


class TestSerialInterface:
    """Test serial interface module."""

    @pytest.mark.parametrize(
        ("x_env", "x_serial", "x_serialx", "x_case"),
        [
            (None, True, False, True),
            (None, False, True, False),
            (None, True, True, True),
            (None, False, False, "exc"),
            ("serial", True, False, True),
            ("serial", False, True, "exc"),
            ("serial", True, True, True),
            ("serial", False, False, "exc"),
            ("serialx", True, False, "exc"),
            ("serialx", False, True, False),
            ("serialx", True, True, False),
            ("serialx", False, False, "exc"),
            ("illegal", True, False, "exc"),
            ("illegal", False, True, "exc"),
            ("illegal", True, True, "exc"),
            ("illegal", False, False, "exc"),
        ],
    )
    def test_import_serials(self, x_env, x_serial, x_serialx, x_case):
        """Test serial/serialx as well as environment variable."""
        with (
            mock.patch.dict(os.environ),
            mock.patch.dict(sys.modules),
        ):
            os.environ.pop("pymodbus_force_serial", None)
            sys.modules.pop("serial", None)
            sys.modules.pop("serialx", None)
            if x_env:
                os.environ["pymodbus_force_serial"] = x_env
            if x_serial:
                sys.modules["serial"] = mock.MagicMock()
            if x_serialx:
                sys.modules["serialx"] = mock.MagicMock()
            if x_case == "exc":
                with pytest.raises((RuntimeError, TypeError)):
                    SerialInterface.select_import_serial()
            else:
                assert x_case == SerialInterface.select_import_serial()
        assert "serial" in sys.modules
        assert "serialx" in sys.modules

    def test_init(self, mock_serial):
        """Test init."""
        SerialInterface()

    def test_properties(self, mock_serial):
        """Test properties."""
        mock_serial.timeout
        mock_serial.timeout = 5
        mock_serial.is_open
        mock_serial.in_waiting
        mock_serial.fileno

    async def test_methods(self, mock_serial):
        """Test external methods."""
        mock_serial.sync_read(5)
        mock_serial.sync_write(b"abcd")
        mock_serial.sync_close()

    async def test_create_serial(self, mock_serial, dummy_protocol):
        """Test external methods."""
        transport, protocol = await SerialInterface().create_serial_connection(
            asyncio.get_running_loop(),
            lambda: dummy_protocol,
            "/dev/null",
            baudrate=9600,
            bytesize=8,
            parity="E",
            stopbits=2,
            timeout=0,
        )
        assert transport
        assert protocol

    async def test_wrong_create_serial(self, mock_serial):
        """Test external methods."""
        with pytest.raises(TypeError):
            await SerialInterface().create_serial_connection(
                asyncio.get_running_loop(),
                mock.MagicMock,
                "/dev/null",
                baudrate=9600,
                bytesize=8,
                parity="E",
                stopbits=2,
                timeout=0,
                no_parm=True,  # zuban: ignore[call-arg]
            )
