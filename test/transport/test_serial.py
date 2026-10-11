"""Test transport."""

import asyncio
import os
import sys
from contextlib import suppress
from functools import partial
from unittest import mock

import pytest

from pymodbus.transport.serialtransport import (
    OldSerialTransport,
    SerialSync,
    create_serial_connection,
)


@mock.patch(
    "pymodbus.transport.serialtransport.pyserial.serial_for_url", mock.MagicMock()
)
class TestTransportSerial:
    """Test transport serial module."""

    async def test_init(self):
        """Test null modem init."""
        OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )

    async def test_loop(self):
        """Test asyncio abstract methods."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        assert comm.loop

    @pytest.mark.parametrize("inx", range(0, 11))
    async def test_abstract_methods(self, inx):
        """Test asyncio abstract methods."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
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
        methods[inx]()  # type: ignore[operator]

    @pytest.mark.parametrize("inx", range(0, 4))
    async def test_external_methods(self, inx):
        """Test external methods."""
        comm = OldSerialTransport(
            mock.MagicMock(), mock.Mock(), "dummy", None, None, None, None, None
        )
        comm.sync_serial.read = mock.MagicMock(return_value="abcd")  # type: ignore[method-assign]
        comm.sync_serial.write = mock.MagicMock(return_value=4)  # type: ignore[method-assign]
        comm.sync_serial.fileno = mock.MagicMock(return_value=2)  # type: ignore[method-assign]
        comm.async_loop.add_writer = mock.MagicMock()
        comm.async_loop.add_reader = mock.MagicMock()
        comm.async_loop.remove_writer = mock.MagicMock()
        comm.async_loop.remove_reader = mock.MagicMock()

        methods = [
            partial(comm.write, b"abcd"),
            partial(comm.flush),
            partial(comm.close),
            partial(comm.abort),
        ]
        methods[inx]()

    def test_serial_sync_methods(self):
        """Test serial sync."""
        transport = SerialSync()
        transport.inter_byte_timeout
        transport.timeout
        transport.write_timeout
        transport.is_open

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_create_serial(self):
        """Test external methods."""
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, "dummy"
        )
        assert transport
        assert protocol
        transport.close()

    @pytest.mark.skipif(
        OldSerialTransport.force_poll, reason="Serial poll not supported"
    )
    async def test_force_poll(self):
        """Test external methods."""
        OldSerialTransport.force_poll = True
        transport, protocol = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, "dummy"
        )
        await asyncio.sleep(0)
        assert transport
        assert protocol
        transport.close()
        OldSerialTransport.force_poll = False

    @pytest.mark.skipif(
        OldSerialTransport.force_poll, reason="Serial poll not supported"
    )
    async def test_write_force_poll(self):
        """Test write with poll."""
        OldSerialTransport.force_poll = True
        transport, _ = await create_serial_connection(
            asyncio.get_running_loop(), mock.Mock, "dummy"
        )
        await asyncio.sleep(0)
        transport.write(b"abcd")
        await asyncio.sleep(0.5)
        transport.close()
        OldSerialTransport.force_poll = False

    async def test_close(self):
        """Test close."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = None  # type: ignore[assignment]
        comm.close()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_polling(self):
        """Test polling."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.read.side_effect = asyncio.CancelledError("test")
        with suppress(asyncio.CancelledError):
            await comm.polling_task()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_poll_task(self):
        """Test polling."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.read.side_effect = SerialSync.SerialException("test")
        await comm.polling_task()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_poll_task2(self):
        """Test polling."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.sync_serial.read.side_effect = SerialSync.SerialException("test")
        await comm.polling_task()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_exception(self):
        """Test write exception."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.side_effect = BlockingIOError("test")
        comm.intern_write_ready()
        comm.sync_serial.write.side_effect = SerialSync.SerialException("test")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_ok(self):
        """Test write exception."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_len(self):
        """Test write exception."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 3
        comm.async_loop.add_writer = mock.Mock()
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.parametrize("polling", [False, True])
    @pytest.mark.parametrize("writes", [(0, 2, 2), (2, 0, 2), (0, 0, 4), (None, 4)])
    async def test_zero_length_write_retains_buffer(self, polling, writes):
        """A nonblocking zero-byte write must not drop a pending RTU frame."""
        loop = mock.MagicMock()
        comm = OldSerialTransport(
            loop, mock.Mock(), "dummy", None, None, None, None, None
        )
        if polling:
            comm.poll_task = mock.Mock()
        serial_write = mock.MagicMock(side_effect=writes)
        comm.intern_write_buffer.append(b"abcd")

        with mock.patch.object(comm.sync_serial, "write", serial_write):
            sent = 0
            for written in writes:
                comm.intern_write_ready()
                assert serial_write.call_args.args[0] == b"abcd"[sent:]
                sent += written or 0
                assert comm.intern_write_buffer == (
                    [b"abcd"[sent:]] if sent < 4 else []
                )
        assert comm.intern_write_buffer == []
        assert serial_write.call_count == len(writes)
        if polling:
            loop.add_writer.assert_not_called()
        else:
            assert loop.add_writer.call_count == len(writes) - 1

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_write_force(self):
        """Test write exception."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.poll_task = True  # type: ignore[assignment]
        comm.sync_serial = mock.MagicMock()
        comm.sync_serial.write.return_value = 3
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(os.name == "nt", reason="Windows not supported")
    async def test_read_ready(self):
        """Test polling."""
        comm = OldSerialTransport(
            asyncio.get_running_loop(),
            mock.Mock(),
            "dummy",
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial = mock.MagicMock()
        comm.intern_protocol = mock.Mock()
        comm.sync_serial.read = mock.Mock()
        comm.sync_serial.read.return_value = b""
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_not_called()
        comm.sync_serial.read.return_value = b"abcd"
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_called_once()

    async def test_import_pyserial(self):
        """Test pyserial not installed."""
        with mock.patch.dict(sys.modules, {"no_modules": None}) as mock_modules:
            del mock_modules["serial"]
            with pytest.raises(RuntimeError):
                OldSerialTransport(
                    asyncio.get_running_loop(),
                    mock.Mock(),
                    "dummy",
                    None,
                    None,
                    None,
                    None,
                    None,
                )
