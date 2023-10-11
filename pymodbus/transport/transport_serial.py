"""asyncio serial support for modbus (based on pyserial)."""
import asyncio
import contextlib
import os
from typing import Tuple


with contextlib.suppress(ImportError):
    import serial


class SerialTransport(asyncio.Transport):
    """An asyncio serial transport."""

    force_poll: bool = False

    def __init__(self, loop, protocol, *args, **kwargs):
        """Initialize."""
        super().__init__()
        self.async_loop = loop
        self._protocol: asyncio.BaseProtocol = protocol
        self.sync_serial = serial.serial_for_url(*args, **kwargs)
        self._write_buffer = []
        self.poll_task = None
        self._poll_wait_time = 0.0005
        self.sync_serial.timeout = 0
        self.sync_serial.write_timeout = 0

    def setup(self):
        """Prepare to read/write"""
        if os.name == "nt" or self.force_poll:
            self.poll_task = asyncio.create_task(self._polling_task())
        else:
            self.async_loop.add_reader(self.sync_serial.fileno(), self._read_ready)
        self.async_loop.call_soon(self._protocol.connection_made, self)

    def close(self, exc=None):
        """Close the transport gracefully."""
        if not self.sync_serial:
            return
        with contextlib.suppress(Exception):
            self.sync_serial.flush()

        self.flush()
        if self.poll_task:
            self.poll_task.cancel()
            _ = asyncio.ensure_future(self.poll_task)
            self.poll_task = None
        else:
            self.async_loop.remove_reader(self.sync_serial.fileno())
        self.sync_serial.close()
        self.sync_serial = None
        with contextlib.suppress(Exception):
            self._protocol.connection_lost(exc)

    def write(self, data):
        """Write some data to the transport."""
        self._write_buffer.append(data)
        if not self.poll_task:
            self.async_loop.add_writer(self.sync_serial.fileno(), self._write_ready)

    def flush(self):
        """Clear output buffer and stops any more data being written"""
        if not self.poll_task:
            self.async_loop.remove_writer(self.sync_serial.fileno())
        self._write_buffer.clear()

    # ------------------------------------------------
    # Dummy methods needed to please asyncio.Transport.
    # ------------------------------------------------
    @property
    def loop(self):
        """Return asyncio event loop."""
        return self.async_loop

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

    def is_closing(self):
        """Return True if the transport is closing or closed."""
        return False

    def abort(self):
        """Close the transport immediately."""
        self.close()

    # ------------------------------------------------

    def _read_ready(self):
        """Test if there are data waiting."""
        try:
            if data := self.sync_serial.read(1024):
                self._protocol.data_received(data)
        except serial.SerialException as exc:
            self.close(exc=exc)

    def _write_ready(self):
        """Asynchronously write buffered data."""
        data = b"".join(self._write_buffer)
        try:
            if (nlen := self.sync_serial.write(data)) < len(data):
                self._write_buffer = [data[nlen:]]
                if not self.poll_task:
                    self.async_loop.add_writer(
                        self.sync_serial.fileno(), self._write_ready
                    )
                return
            self.flush()
        except (BlockingIOError, InterruptedError):
            return
        except serial.SerialException as exc:
            self.close(exc=exc)

    async def _polling_task(self):
        """Poll and try to read/write."""
        try:
            while True:
                await asyncio.sleep(self._poll_wait_time)
                while self._write_buffer:
                    self._write_ready()
                if self.sync_serial.in_waiting:
                    self._read_ready()
        except serial.SerialException as exc:
            self.close(exc=exc)
        except asyncio.CancelledError:
            pass


async def create_serial_connection(loop, protocol_factory, *args, **kwargs):
    """Create a connection to a new serial port instance."""
    protocol = protocol_factory()
    transport = SerialTransport(loop, protocol, *args, **kwargs)
    loop.call_soon(transport.setup)
    return transport, protocol
