"""asyncio serial support for modbus (based on pyserial)."""
import asyncio
import contextlib
import os
from typing import Tuple


with contextlib.suppress(ImportError):
    import serial


class SerialTransport(asyncio.Transport):
    """An asyncio serial transport."""

    def __init__(self, loop, protocol, *args, **kwargs):
        """Initialize."""
        super().__init__()
        self.async_loop = loop
        self._protocol = protocol
        self.sync_serial = serial.serial_for_url(*args, **kwargs)
        self._closing = False
        self._write_buffer = []
        self.set_write_buffer_limits()
        self._has_reader = False
        self._has_writer = False
        self._poll_wait_time = 0.0005

        # Asynchronous I/O requires non-blocking devices
        self.sync_serial.timeout = 0
        self.sync_serial.write_timeout = 0
        loop.call_soon(protocol.connection_made, self)
        loop.call_soon(self._ensure_reader)

    # ------------------------------------------------
    # Dummy methods needed to please asyncio.Transport.
    # ------------------------------------------------
    @property
    def loop(self):
        """Return asyncio event loop."""
        return self._protocol.loop

    def get_protocol(self) -> asyncio.BaseProtocol:
        """Return protocol"""
        return self._protocol

    def set_protocol(self, protocol: asyncio.BaseProtocol) -> None:
        """Set protocol"""
        self._protocol = protocol

    def get_write_buffer_limits(self) -> Tuple[int, int]:
        """Return buffer sizes"""
        return (1, 1024)

    def can_write_eof(self):
        """Return Serial do not support end-of-file."""
        return False

    def write_eof(self):
        """Write end of file marker."""

    def set_write_buffer_limits(self, high=None, low=None):
        """Set the high- and low-water limits for write flow control."""

    def get_write_buffer_size(self):
        """Return The number of bytes in the write buffer."""
        return len(self._write_buffer)

    def is_reading(self) -> bool:
        """Return true if read is active."""
        return True

    def pause_reading(self):
        """Pause receiver."""

    def resume_reading(self):
        """Resume receiver."""

    # ------------------------------------------------

    def is_closing(self):
        """Return True if the transport is closing or closed."""
        return self._closing

    def close(self):
        """Close the transport gracefully."""
        if self._closing:
            return
        self._closing = True
        self._remove_reader()
        self._remove_writer()
        self.async_loop.call_soon(self._call_connection_lost, None)

    def _read_ready(self):
        """Test if there are data waiting."""
        try:
            data = self.sync_serial.read(1024)
        except serial.SerialException as exc:
            self._protocol.loop.call_soon(self._call_connection_lost, exc)
            self.close()
        else:
            if data:
                self._protocol.data_received(data)

    def write(self, data):
        """Write some data to the transport."""
        if self._closing:
            return

        self._write_buffer.append(data)
        self._ensure_writer()

    def abort(self):
        """Close the transport immediately."""
        self.close()

    def flush(self):
        """Clear output buffer and stops any more data being written"""
        self._remove_writer()
        self._write_buffer.clear()

    def _write_ready(self):
        """Asynchronously write buffered data."""
        data = b"".join(self._write_buffer)
        assert data, "Write buffer should not be empty"

        self._write_buffer.clear()

        try:
            nlen = self.sync_serial.write(data)
        except (BlockingIOError, InterruptedError):
            self._write_buffer.append(data)
        except serial.SerialException as exc:
            self._protocol.loop.call_soon(self._call_connection_lost, exc)
            self.abort()
        else:
            if nlen == len(data):
                assert not self.get_write_buffer_size()
                self._remove_writer()
                if self._closing and not self.get_write_buffer_size():
                    self.close()
                return

            assert 0 <= nlen < len(data)
            data = data[nlen:]
            self._write_buffer.append(data)  # Try again later
            assert self._has_writer

    if os.name == "nt":

        def _poll_read(self):
            if self._has_reader and not self._closing:
                try:
                    self._has_reader = self.async_loop.call_later(
                        self._poll_wait_time, self._poll_read
                    )
                    if self.sync_serial.in_waiting:
                        self._read_ready()
                except serial.SerialException as exc:
                    self.async_loop.call_soon(self._call_connection_lost, exc)
                    self.abort()

        def _ensure_reader(self):
            if not self._has_reader and not self._closing:
                self._has_reader = self.async_loop.call_later(
                    self._poll_wait_time, self._poll_read
                )

        def _remove_reader(self):
            if self._has_reader:
                self._has_reader.cancel()
            self._has_reader = False

        def _poll_write(self):
            if self._has_writer and not self._closing:
                self._has_writer = self.async_loop.call_later(
                    self._poll_wait_time, self._poll_write
                )
                self._write_ready()

        def _ensure_writer(self):
            if not self._has_writer and not self._closing:
                self._has_writer = self.async_loop.call_soon(self._poll_write)

        def _remove_writer(self):
            if self._has_writer:
                self._has_writer.cancel()
            self._has_writer = False

    else:

        def _ensure_reader(self):
            if (not self._has_reader) and (not self._closing):
                self.async_loop.add_reader(self.sync_serial.fileno(), self._read_ready)
                self._has_reader = True

        def _remove_reader(self):
            if self._has_reader:
                self.async_loop.remove_reader(self.sync_serial.fileno())
                self._has_reader = False

        def _ensure_writer(self):
            if (not self._has_writer) and (not self._closing):
                self.async_loop.add_writer(self.sync_serial.fileno(), self._write_ready)
                self._has_writer = True

        def _remove_writer(self):
            if self._has_writer:
                self.async_loop.remove_writer(self.sync_serial.fileno())
                self._has_writer = False

    def _call_connection_lost(self, exc):
        """Close the connection."""
        assert self._closing
        assert not self._has_writer
        assert not self._has_reader
        if self.sync_serial:
            with contextlib.suppress(Exception):
                self.sync_serial.flush()

            self.sync_serial.close()
            self.sync_serial = None
        if self._protocol:
            with contextlib.suppress(Exception):
                self._protocol.connection_lost(exc)

            self._write_buffer.clear()
        self._write_buffer.clear()


async def create_serial_connection(loop, protocol_factory, *args, **kwargs):
    """Create a connection to a new serial port instance."""
    protocol = protocol_factory()
    transport = SerialTransport(loop, protocol, *args, **kwargs)
    return transport, protocol
