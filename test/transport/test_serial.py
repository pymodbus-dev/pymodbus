"""Test transport."""
import asyncio
import contextlib
import os
from functools import partial
from unittest import mock

import pytest
import serial
from serial.rs485 import RS485Settings

from pymodbus.transport.serialtransport import (
    SerialTransport,
    create_serial_connection,
)


@mock.patch(
    "pymodbus.transport.serialtransport.serial.serial_for_url", mock.MagicMock()
)
@mock.patch(
    "pymodbus.transport.serialtransport.serial.rs485.RS485", mock.MagicMock()
)
class TestTransportSerial:
    """Test transport serial module."""

    async def test_init(self):
        """Test null modem init."""
        SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")

    async def test_loop(self):
        """Test asyncio abstract methods."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        assert comm.loop

    @pytest.mark.parametrize("inx", range(0, 11))
    async def test_abstract_methods(self, inx):
        """Test asyncio abstract methods."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        methods = [
            partial(comm.get_protocol),
            partial(comm.set_protocol, None),
            partial(comm.get_write_buffer_limits),
            partial(comm.can_write_eof),
            partial(comm.write_eof),
            partial(comm.set_write_buffer_limits, 1024, 1),
            partial(comm.get_write_buffer_size),
            partial(comm.is_reading),
            partial(comm.pause_reading),
            partial(comm.resume_reading),
            partial(comm.is_closing),
        ]
        methods[inx]()

    @pytest.mark.parametrize("inx", range(0, 4))
    async def test_external_methods(self, inx):
        """Test external methods."""
        comm = SerialTransport(mock.MagicMock(), mock.Mock(), None, "dummy")
        comm.sync_serial.read = mock.MagicMock(return_value="abcd")
        comm.sync_serial.write = mock.MagicMock(return_value=4)
        comm.sync_serial.fileno = mock.MagicMock(return_value=2)
        comm.async_loop.add_writer = mock.MagicMock()
        comm.async_loop.add_reader = mock.MagicMock()
        comm.async_loop.remove_writer = mock.MagicMock()
        comm.async_loop.remove_reader = mock.MagicMock()
        comm.sync_serial.in_waiting = False

        methods = [
            partial(comm.write, b"abcd"),
            partial(comm.flush),
            partial(comm.close),
            partial(comm.abort),
        ]
        methods[inx]()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_create_serial(self):
        """Test external methods."""
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, None, url="dummy"
        )
        assert transport
        assert protocol
        transport.close()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_create_rs485_serial(self):
        """Test external methods."""
        settings = RS485Settings(rts_level_for_rx=True, rts_level_for_tx=True, delay_before_rx=0.4)
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, settings, url="dummy"
        )
        assert transport
        assert protocol
        assert transport.sync_serial.rs485_mode
        assert transport.sync_serial.rs485_mode == settings
        transport.close()

    async def test_force_poll(self):
        """Test external methods."""
        SerialTransport.force_poll = True
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, None, url="dummy"
        )
        await asyncio.sleep(0)
        assert transport
        assert protocol
        transport.close()
        SerialTransport.force_poll = False


    async def test_write_force_poll(self):
        """Test write with poll."""
        SerialTransport.force_poll = True
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, None, url="dummy"
        )
        await asyncio.sleep(0)
        transport.write(b"abcd")
        await asyncio.sleep(0.5)
        transport.close()
        SerialTransport.force_poll = False

    async def test_close(self):
        """Test close."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = None
        comm.close()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_polling(self):
        """Test polling."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.read.side_effect = asyncio.CancelledError("test")
        with contextlib.suppress(asyncio.CancelledError):
            await comm.polling_task()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_poll_task(self):
        """Test polling."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.read.side_effect = serial.SerialException("test")
        await comm.polling_task()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_poll_task2(self):
        """Test polling."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.sync_serial.read.side_effect = serial.SerialException("test")
        await comm.polling_task()


    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_exception(self):
        """Test write exception."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.side_effect = BlockingIOError("test")
        comm.intern_write_ready()
        comm.sync_serial.write.side_effect = serial.SerialException("test")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_ok(self):
        """Test write exception."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_len(self):
        """Test write exception."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 3
        comm.async_loop.add_writer = mock.Mock()
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_force(self):
        """Test write exception."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.poll_task = True
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 3
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_read_ready(self):
        """Test polling."""
        comm = SerialTransport(asyncio.get_running_loop(), mock.Mock(), None, "dummy")
        comm.sync_serial = mock.MagicMock()
        comm.intern_protocol = mock.Mock()
        comm.sync_serial.read = mock.Mock()
        comm.sync_serial.read.return_value = b''
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_not_called()
        comm.sync_serial.read.return_value = b'abcd'
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_called_once()
