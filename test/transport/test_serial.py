"""Test transport."""

import asyncio
import sys
from contextlib import suppress
from functools import partial
from unittest import mock

import pytest

from pymodbus.transport.serialtransport import (
    SerialInterface,
    SerialTransport,
)


class TestTransportSerial:
    """Test transport serial module."""

    @pytest.fixture
    def mock_use_ser_2lib(self):
        """Patch select_import_serial."""
        with mock.patch(
            "pymodbus.transport.serialtransport.SerialInterface.select_import_serial",
            autospec=True,
        ) as mock_lib:
            mock_lib.return_value = True
            yield

    async def test_init(self, mock_serial, dummy_protocol):
        """Test null modem init."""
        SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )

    async def test_loop(self, mock_serial, dummy_protocol):
        """Test asyncio abstract methods."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        assert comm.loop

    @pytest.mark.parametrize("inx", range(0, 11))
    async def test_abstract_methods(self, inx, mock_serial, dummy_protocol):
        """Test asyncio abstract methods."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
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
    async def test_external_methods(self, inx, mock_serial, dummy_protocol):
        """Test external methods."""
        comm = SerialTransport(
            mock.MagicMock(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        mock.patch.object(comm.sync_serial.serial, "read", new_callable=lambda: "abcd")
        mock.patch.object(comm.sync_serial.serial, "write", new_callable=lambda: 4)
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

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Serial poll not supported")
    async def test_force_poll(self, mock_serial, dummy_protocol):
        """Test external methods."""
        with mock.patch(
            "pymodbus.transport.serialtransport.SerialTransport.force_poll"
        ):
            for force_poll in (True, False):
                SerialTransport.force_poll = force_poll
                transport, protocol = await mock_serial.create_serial_connection(
                    asyncio.get_running_loop(), lambda: dummy_protocol, "dummy"
                )
                await asyncio.sleep(0)
                assert transport
                assert protocol
                transport.close()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Serial poll not supported")
    async def test_write_force_poll(self, mock_serial, dummy_protocol):
        """Test write with poll."""
        with mock.patch(
            "pymodbus.transport.serialtransport.SerialTransport.force_poll"
        ):
            SerialTransport.force_poll = True
            transport, _ = await SerialInterface().create_serial_connection(
                asyncio.get_running_loop(), lambda: dummy_protocol, "dummy"
            )
            await asyncio.sleep(0)
            transport.write(b"abcd")
            await asyncio.sleep(0.5)
            transport.close()

    async def test_close(self, mock_serial, dummy_protocol):
        """Test close."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.close()
        assert not comm.sync_serial
        comm.close()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Serial poll not supported")
    async def test_polling(self, mock_serial, dummy_protocol):
        """Test polling."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.read.side_effect = asyncio.CancelledError("test")
        with suppress(asyncio.CancelledError):
            await comm.polling_task()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_poll_task(self, mock_serial, dummy_protocol):
        """Test polling."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.read.side_effect = comm.sync_serial.SerialException(
            "test"
        )
        type(comm.sync_serial).in_waiting = mock.PropertyMock(side_effect=[0, 1])  # type: ignore[method-assign]
        await comm.polling_task()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Serial poll not supported")
    async def test_poll_task2(self, mock_serial, dummy_protocol):
        """Test polling."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.sync_serial.serial.read.side_effect = comm.sync_serial.SerialException(
            "test"
        )
        type(comm.sync_serial).in_waiting = mock.PropertyMock(side_effect=[0, 1])  # type: ignore[method-assign]
        await comm.polling_task()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_write_exception(self, mock_serial, dummy_protocol):
        """Test write exception."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.write.side_effect = BlockingIOError("test")
        comm.intern_write_ready()
        comm.sync_serial.serial.write.side_effect = mock_serial.SerialException("test")
        comm.intern_write_ready()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_write_ok(self, mock_serial, dummy_protocol):
        """Test write exception."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.write.return_value = 4
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_write_len(self, mock_serial, dummy_protocol):
        """Test write exception."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.sync_serial.serial.write.return_value = 3
        comm.async_loop.add_writer = mock.Mock()
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.parametrize("polling", [False, True])
    @pytest.mark.parametrize("writes", [(0, 2, 2), (2, 0, 2), (0, 0, 4), (None, 4)])
    async def test_zero_length_write_retains_buffer(
        self, polling, writes, mock_serial, dummy_protocol
    ):
        """A nonblocking zero-byte write must not drop a pending RTU frame."""
        loop = mock.MagicMock()
        comm = SerialTransport(
            loop,
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        if polling:
            comm.poll_task = mock.Mock()
        serial_write = mock.MagicMock(side_effect=writes)
        comm.intern_write_buffer.append(b"abcd")

        with mock.patch.object(comm.sync_serial.serial, "write", serial_write):
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

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_write_force(self, mock_serial, dummy_protocol):
        """Test write exception."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.poll_task = True  # type: ignore[assignment]
        comm.sync_serial.serial.write.return_value = 3
        comm.intern_write_buffer.append(b"abcd")
        comm.intern_write_ready()

    @pytest.mark.skipif(SerialTransport.force_poll, reason="Windows not supported")
    async def test_read_ready(self, mock_serial, dummy_protocol):
        """Test polling."""
        comm = SerialTransport(
            asyncio.get_running_loop(),
            dummy_protocol,
            "dummy",
            None,
            None,
            None,
            None,
            None,
            None,
        )
        comm.intern_protocol = mock.Mock()
        comm.sync_serial.serial.read = mock.Mock()
        comm.sync_serial.serial.read.return_value = b""
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_not_called()
        comm.sync_serial.serial.read.return_value = b"abcd"
        comm.intern_read_ready()
        comm.intern_protocol.data_received.assert_called_once()

    async def test_import_pyserial(self):
        """Test pyserial not installed."""
        with mock.patch.dict(sys.modules, {"no_modules": None}) as mock_modules:
            del mock_modules["serial"]
            with pytest.raises(RuntimeError):
                SerialTransport(
                    asyncio.get_running_loop(),
                    mock.Mock(),
                    "dummy",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
