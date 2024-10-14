"""Modbus client async serial communication."""
from __future__ import annotations

import contextlib
import sys
import time
from collections.abc import Callable
from functools import partial

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType
from pymodbus.utilities import ModbusTransactionState


with contextlib.suppress(ImportError):
    import serial


class AsyncModbusSerialClient(ModbusBaseClient):
    """**AsyncModbusSerialClient**.

    Fixed parameters:

    :param port: Serial port used for communication.

    Optional parameters:

    :param framer: Framer name, default FramerType.RTU
    :param baudrate: Bits per second.
    :param bytesize: Number of bits per byte 7-8.
    :param parity: 'E'ven, 'O'dd or 'N'one
    :param stopbits: Number of stop bits 1, 1.5, 2.
    :param handle_local_echo: Discard local echo from dongle.
    :param name: Set communication name, used in logging
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param timeout: Timeout for connecting and receiving data, in seconds.
    :param retries: Max number of retries per request.
    :param on_connect_callback: Function that will be called just before a connection attempt.

    .. tip::
        **reconnect_delay** doubles automatically with each unsuccessful connect, from
        **reconnect_delay** to **reconnect_delay_max**.
        Set `reconnect_delay=0` to avoid automatic reconnection.

    Example::

        from pymodbus.client import AsyncModbusSerialClient

        async def run():
            client = AsyncModbusSerialClient("dev/serial0")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        port: str,
        framer: FramerType = FramerType.RTU,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        handle_local_echo: bool = False,
        name: str = "comm",
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
        on_connect_callback: Callable[[bool], None] | None = None,
    ) -> None:
        """Initialize Asyncio Modbus Serial Client."""
        if "serial" not in sys.modules:
            raise RuntimeError(
                "Serial client requires pyserial "
                'Please install with "pip install pyserial" and try again.'
            )
        self.comm_params = CommParams(
            comm_type=CommType.SERIAL,
            host=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            handle_local_echo=handle_local_echo,
            comm_name=name,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        ModbusBaseClient.__init__(
            self,
            framer,
            retries,
            on_connect_callback,
        )


class ModbusSerialClient(ModbusBaseSyncClient):
    """**ModbusSerialClient**.

    Fixed parameters:

    :param port: Serial port used for communication.

    Optional parameters:

    :param framer: Framer name, default FramerType.RTU
    :param baudrate: Bits per second.
    :param bytesize: Number of bits per byte 7-8.
    :param parity: 'E'ven, 'O'dd or 'N'one
    :param stopbits: Number of stop bits 0-2.
    :param handle_local_echo: Discard local echo from dongle.
    :param name: Set communication name, used in logging
    :param reconnect_delay: Not used in the sync client
    :param reconnect_delay_max: Not used in the sync client
    :param timeout: Timeout for connecting and receiving data, in seconds.
    :param retries: Max number of retries per request.

    Note that unlike the async client, the sync client does not perform
    retries. If the connection has closed, the client will attempt to reconnect
    once before executing each read/write request, and will raise a
    ConnectionException if this fails.

    Example::

        from pymodbus.client import ModbusSerialClient

        def run():
            client = ModbusSerialClient("dev/serial0")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    state = ModbusTransactionState.IDLE
    inter_byte_timeout: float = 0
    silent_interval: float = 0

    def __init__(  # pylint: disable=too-many-arguments
        self,
        port: str,
        framer: FramerType = FramerType.RTU,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        handle_local_echo: bool = False,
        name: str = "comm",
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
    ) -> None:
        """Initialize Modbus Serial Client."""
        self.comm_params = CommParams(
            comm_type=CommType.SERIAL,
            host=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            handle_local_echo=handle_local_echo,
            comm_name=name,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        super().__init__(
            framer,
            retries,
        )
        if "serial" not in sys.modules:
            raise RuntimeError(
                "Serial client requires pyserial "
                'Please install with "pip install pyserial" and try again.'
            )
        self.socket: serial.Serial | None = None
        self.last_frame_end = None
        self._t0 = float(1 + bytesize + stopbits) / baudrate

        # Check every 4 bytes / 2 registers if the reading is ready
        self._recv_interval = self._t0 * 4
        # Set a minimum of 1ms for high baudrates
        self._recv_interval = max(self._recv_interval, 0.001)

        if baudrate > 19200:
            self.silent_interval = 1.75 / 1000  # ms
        else:
            self.inter_byte_timeout = 1.5 * self._t0
            self.silent_interval = 3.5 * self._t0
        self.silent_interval = round(self.silent_interval, 6)

    @property
    def connected(self) -> bool:
        """Check if socket exists."""
        return self.socket is not None

    def connect(self) -> bool:
        """Connect to the modbus serial server."""
        if self.socket:
            return True
        try:
            self.socket = serial.serial_for_url(
                self.comm_params.host,
                timeout=self.comm_params.timeout_connect,
                bytesize=self.comm_params.bytesize,
                stopbits=self.comm_params.stopbits,
                baudrate=self.comm_params.baudrate,
                parity=self.comm_params.parity,
                exclusive=True,
            )
            self.socket.inter_byte_timeout = self.inter_byte_timeout
            self.last_frame_end = None
        # except serial.SerialException as msg:
        # pyserial raises undocumented exceptions like termios
        except Exception as msg:  # pylint: disable=broad-exception-caught
            Log.error("{}", msg)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _in_waiting(self):
        """Return waiting bytes."""
        return getattr(self.socket, "in_waiting") if hasattr(self.socket, "in_waiting") else getattr(self.socket, "inWaiting")()

    def _send(self, request: bytes) -> int:
        """Send data on the underlying socket.

        If receive buffer still holds some data then flush it.

        Sleep if last send finished less than 3.5 character times ago.
        """
        super()._start_send()
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            if waitingbytes := self._in_waiting():
                result = self.socket.read(waitingbytes)
                Log.warning("Cleanup recv buffer before send: {}", result, ":hex")
            if (size := self.socket.write(request)) is None:
                size = 0
            return size
        return 0

    def send(self, request: bytes) -> int:
        """Send data on the underlying socket."""
        start = time.time()
        if hasattr(self,"ctx"):
          timeout = start + self.ctx.comm_params.timeout_connect
        else:
            timeout = start + self.comm_params.timeout_connect
        while self.state != ModbusTransactionState.IDLE:
            if self.state == ModbusTransactionState.TRANSACTION_COMPLETE:
                timestamp = round(time.time(), 6)
                Log.debug(
                    "Changing state to IDLE - Last Frame End - {} Current Time stamp - {}",
                    self.last_frame_end,
                    timestamp,
                )
                if self.last_frame_end:
                    idle_time = self.idle_time()
                    if round(timestamp - idle_time, 6) <= self.silent_interval:
                        Log.debug(
                            "Waiting for 3.5 char before next send - {} ms",
                            self.silent_interval * 1000,
                        )
                        time.sleep(self.silent_interval)
                else:
                    # Recovering from last error ??
                    time.sleep(self.silent_interval)
                self.state = ModbusTransactionState.IDLE
            elif self.state == ModbusTransactionState.RETRYING:
                # Simple lets settle down!!!
                # To check for higher baudrates
                time.sleep(self.comm_params.timeout_connect)
                break
            elif time.time() > timeout:
                Log.debug(
                    "Spent more time than the read time out, "
                    "resetting the transaction to IDLE"
                )
                self.state = ModbusTransactionState.IDLE
            else:
                Log.debug("Sleeping")
                time.sleep(self.silent_interval)
        size = self._send(request)
        self.last_frame_end = round(time.time(), 6)
        return size

    def _wait_for_data(self) -> int:
        """Wait for data."""
        size = 0
        more_data = False
        condition = partial(
            lambda start, timeout: (time.time() - start) <= timeout,
            timeout=self.comm_params.timeout_connect,
        )
        start = time.time()
        while condition(start):
            available = self._in_waiting()
            if (more_data and not available) or (more_data and available == size):
                break
            if available and available != size:
                more_data = True
                size = available
            time.sleep(self._recv_interval)
        return size

    def recv(self, size: int | None) -> bytes:
        """Read data from the underlying descriptor."""
        if not self.socket:
            raise ConnectionException(str(self))
        if size is None:
            size = self._wait_for_data()
        if size > self._in_waiting():
            self._wait_for_data()
        result = self.socket.read(size)
        self.last_frame_end = round(time.time(), 6)
        return result

    def is_socket_open(self) -> bool:
        """Check if socket is open."""
        if self.socket:
            return self.socket.is_open
        return False

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"framer={self.framer}, timeout={self.comm_params.timeout_connect}>"
        )
