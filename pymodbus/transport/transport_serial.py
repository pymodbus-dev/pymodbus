"""asyncio serial support for modbus (based on pyserial)."""
import asyncio
import contextlib
import os
from typing import Tuple


with contextlib.suppress(ImportError):
    import serial


class SerialTransport(asyncio.Transport):
    """An asyncio transport model of a serial communication channel."""

    def __init__(self, loop, protocol, serial_instance):
        """Initialize."""
        super().__init__()
        self._loop = loop
        self._protocol = protocol
        self._serial = serial_instance
        self._closing = False
        self._write_buffer = []
        self.set_write_buffer_limits()
        self._has_reader = False
        self._has_writer = False
        self._poll_wait_time = 0.0005

        # Asynchronous I/O requires non-blocking devices
        self._serial.timeout = 0
        self._serial.write_timeout = 0
        loop.call_soon(protocol.connection_made, self)
        loop.call_soon(self._ensure_reader)

    # ------------------------------------------------
    # Dummy methods needed to please asyncio.Transport.
    # ------------------------------------------------
    @property
    def loop(self):
        """Return asyncio event loop."""
        return self._loop

    def get_protocol(self) -> asyncio.BaseProtocol:
        """Return protocol"""
        return self._protocol

    def set_protocol(self, protocol: asyncio.BaseProtocol) -> None:
        """Set protocol"""
        self._protocol = protocol

    def get_write_buffer_limits(self) -> Tuple[int, int]:
        """Return buffer sizes"""
        return (0, 1024)

    def can_write_eof(self):
        """Return Serial do not support end-of-file."""
        return False

    def write_eof(self):
        """Write end of file marker."""

    def is_reading(self) -> bool:
        """Return true if read is active."""
        return True

    def pause_reading(self):
        """Pause receiver."""

    def resume_reading(self):
        """Resume receiver."""

    def set_write_buffer_limits(self, high=None, low=None):
        """Set the high- and low-water limits for write flow control."""

    def get_write_buffer_size(self):
        """Return The number of bytes in the write buffer."""
        return len(self._write_buffer)

    # ------------------------------------------------

    def xget_extra_info(self, name, default=None):
        """Get optional transport information.

        Currently only "serial" is available.
        """
        if name == "serial":
            return self._serial
        return default

    def is_closing(self):
        """Return True if the transport is closing or closed."""
        return self._closing

    def close(self):
        """Close the transport gracefully.

        Any buffered data will be written asynchronously. No more data
        will be received and further writes will be silently ignored.
        After all buffered data is flushed, the protocol's
        connection_lost() method will be called with None as its
        argument.
        """
        if not self._closing:
            self._close(None)

    def _read_ready(self):
        """Test if there are data waiting."""
        try:
            data = self._serial.read(1024)
        except serial.SerialException as exc:
            self._close(exc=exc)
        else:
            if data:
                self._protocol.data_received(data)

    def write(self, data):
        """Write some data to the transport.

        This method does not block; it buffers the data and arranges
        for it to be sent out asynchronously.  Writes made after the
        transport has been closed will be ignored.
        """
        if self._closing:
            return

        if not self.get_write_buffer_size():
            self._write_buffer.append(data)
            self._ensure_writer()
        else:
            self._write_buffer.append(data)

    def abort(self):
        """Close the transport immediately.

        Pending operations will not be given opportunity to complete,
        and buffered data will be lost. No more data will be received
        and further writes will be ignored.  The protocol's
        connection_lost() method will eventually be called.
        """
        self._abort(None)

    def flush(self):
        """Clear output buffer and stops any more data being written"""
        self._remove_writer()
        self._write_buffer.clear()

    def _write_ready(self):
        """Asynchronously write buffered data.

        This method is called back asynchronously as a writer
        registered with the asyncio event-loop against the
        underlying file descriptor for the serial port.

        Should the write-buffer become empty if this method
        is invoked while the transport is closing, the protocol's
        connection_lost() method will be called with None as its
        argument.
        """
        data = b"".join(self._write_buffer)
        assert data, "Write buffer should not be empty"

        self._write_buffer.clear()

        try:
            nlen = self._serial.write(data)
        except (BlockingIOError, InterruptedError):
            self._write_buffer.append(data)
        except serial.SerialException as exc:
            self._fatal_error(exc, "Fatal write error on serial transport")
        else:
            if nlen == len(data):
                assert not self.get_write_buffer_size()
                self._remove_writer()
                if self._closing and not self.get_write_buffer_size():
                    self._close()
                return

            assert 0 <= nlen < len(data)
            data = data[nlen:]
            self._write_buffer.append(data)  # Try again later
            assert self._has_writer

    if os.name == "nt":

        def _poll_read(self):
            if self._has_reader and not self._closing:
                try:
                    self._has_reader = self._loop.call_later(
                        self._poll_wait_time, self._poll_read
                    )
                    if self._serial.in_waiting:
                        self._read_ready()
                except serial.SerialException as exc:
                    self._fatal_error(exc, "Fatal write error on serial transport")

        def _ensure_reader(self):
            if not self._has_reader and not self._closing:
                self._has_reader = self._loop.call_later(
                    self._poll_wait_time, self._poll_read
                )

        def _remove_reader(self):
            if self._has_reader:
                self._has_reader.cancel()
            self._has_reader = False

        def _poll_write(self):
            if self._has_writer and not self._closing:
                self._has_writer = self._loop.call_later(
                    self._poll_wait_time, self._poll_write
                )
                self._write_ready()

        def _ensure_writer(self):
            if not self._has_writer and not self._closing:
                self._has_writer = self._loop.call_soon(self._poll_write)

        def _remove_writer(self):
            if self._has_writer:
                self._has_writer.cancel()
            self._has_writer = False

    else:

        def _ensure_reader(self):
            if (not self._has_reader) and (not self._closing):
                self._loop.add_reader(self._serial.fileno(), self._read_ready)
                self._has_reader = True

        def _remove_reader(self):
            if self._has_reader:
                self._loop.remove_reader(self._serial.fileno())
                self._has_reader = False

        def _ensure_writer(self):
            if (not self._has_writer) and (not self._closing):
                self._loop.add_writer(self._serial.fileno(), self._write_ready)
                self._has_writer = True

        def _remove_writer(self):
            if self._has_writer:
                self._loop.remove_writer(self._serial.fileno())
                self._has_writer = False

    def _fatal_error(self, exc, message="Fatal error on serial transport"):
        """Report a fatal error to the event-loop and abort the transport."""
        self._loop.call_exception_handler(
            {
                "message": message,
                "exception": exc,
                "transport": self,
                "protocol": self._protocol,
            }
        )
        self._abort(exc)

    def _close(self, exc=None):
        """Close the transport gracefully.

        If the write buffer is already empty, writing will be
        stopped immediately and a call to the protocol's
        connection_lost() method scheduled.

        If the write buffer is not already empty, the
        asynchronous writing will continue, and the _write_ready
        method will call this _close method again when the
        buffer has been flushed completely.
        """
        self._closing = True
        self._remove_reader()
        if not self.get_write_buffer_size():
            self._remove_writer()
            self._loop.call_soon(self._call_connection_lost, exc)

    def _abort(self, exc):
        """Close the transport immediately.

        Pending operations will not be given opportunity to complete,
        and buffered data will be lost. No more data will be received
        and further writes will be ignored.  The protocol's
        connection_lost() method will eventually be called with the
        passed exception.
        """
        self._closing = True
        self._remove_reader()
        self._remove_writer()  # Pending buffered data will not be written
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        """Close the connection.

        Informs the protocol through connection_lost() and clears
        pending buffers and closes the serial connection.
        """
        assert self._closing
        assert not self._has_writer
        assert not self._has_reader
        if self._serial:
            with contextlib.suppress(Exception):
                self._serial.flush()

            self._serial.close()
            self._serial = None
        if self._protocol:
            with contextlib.suppress(Exception):
                self._protocol.connection_lost(exc)

            self._write_buffer.clear()
        self._write_buffer.clear()
        self._loop = None


async def create_serial_connection(loop, protocol_factory, *args, **kwargs):
    """Create a connection to a new serial port instance."""
    serial_instance = serial.serial_for_url(*args, **kwargs)
    protocol = protocol_factory()
    transport = SerialTransport(loop, protocol, serial_instance)
    return transport, protocol
