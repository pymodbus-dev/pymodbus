"""Modbus client async serial communication."""
from __future__ import annotations

import asyncio
import time
from functools import partial
from typing import Any

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import Framer
from pymodbus.logging import Log
from pymodbus.transport import CommType
from pymodbus.utilities import ModbusTransactionState


try:
    import serial

    PYSERIAL_MISSING = False
except ImportError:
    PYSERIAL_MISSING = True


class AsyncModbusSerialClient(ModbusBaseClient, asyncio.Protocol):
    """**AsyncModbusSerialClient**.

    Fixed parameters:

    :param port: Serial port used for communication.

    Optional parameters:

    :param baudrate: Bits per second.
    :param bytesize: Number of bits per byte 7-8.
    :param parity: 'E'ven, 'O'dd or 'N'one
    :param stopbits: Number of stop bits 1, 1.5, 2.
    :param handle_local_echo: Discard local echo from dongle.

    Common optional parameters:

    :param framer: Framer enum name
    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    Example::

        from pymodbus.client import AsyncModbusSerialClient

        async def run():
            client = AsyncModbusSerialClient("dev/serial0")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(
        self,
        port: str,
        framer: Framer = Framer.RTU,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus Serial Client."""
        if PYSERIAL_MISSING:
            raise RuntimeError(
                "Serial client requires pyserial "
                'Please install with "pip install pyserial" and try again.'
            )
        asyncio.Protocol.__init__(self)
        ModbusBaseClient.__init__(
            self,
            framer,
            CommType=CommType.SERIAL,
            host=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            **kwargs,
        )

    async def connect(self) -> bool:
        """Connect Async client."""
        self.reset_delay()
        Log.debug("Connecting to {}.", self.comm_params.host)
        return await self.transport_connect()

    def close(self, reconnect: bool = False) -> None:
        """Close connection."""
        super().close(reconnect=reconnect)


class ModbusSerialClient(ModbusBaseSyncClient):
    """**ModbusSerialClient**.

    Fixed parameters:

    :param port: Serial port used for communication.

    Optional parameters:

    :param baudrate: Bits per second.
    :param bytesize: Number of bits per byte 7-8.
    :param parity: 'E'ven, 'O'dd or 'N'one
    :param stopbits: Number of stop bits 0-2.
    :param handle_local_echo: Discard local echo from dongle.

    Common optional parameters:

    :param framer: Framer enum name
    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param close_comm_on_error: Close connection on error.
    :param strict: Strict timing, 1.5 character between requests.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    Example::

        from pymodbus.client import ModbusSerialClient

        def run():
            client = ModbusSerialClient("dev/serial0")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.

    Remark: There are no automatic reconnect as with AsyncModbusSerialClient
    """

    state = ModbusTransactionState.IDLE
    inter_char_timeout: float = 0
    silent_interval: float = 0

    def __init__(
        self,
        port: str,
        framer: Framer = Framer.RTU,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus Serial Client."""
        super().__init__(
            framer,
            CommType=CommType.SERIAL,
            host=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            **kwargs,
        )
        self.socket = None

        self.last_frame_end = None

        self._t0 = float(1 + bytesize + stopbits) / baudrate

        # Check every 4 bytes / 2 registers if the reading is ready
        self._recv_interval = self._t0 * 4
        # Set a minimum of 1ms for high baudrates
        self._recv_interval = max(self._recv_interval, 0.001)

        if baudrate > 19200:
            self.silent_interval = 1.75 / 1000  # ms
        else:
            self.inter_char_timeout = 1.5 * self._t0
            self.silent_interval = 3.5 * self._t0
        self.silent_interval = round(self.silent_interval, 6)

    @property
    def connected(self):
        """Connect internal."""
        return self.connect()

    def connect(self):  # pylint: disable=invalid-overridden-method
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
            )
            if self.params.strict:
                self.socket.interCharTimeout = self.inter_char_timeout
            self.last_frame_end = None
        except serial.SerialException as msg:
            Log.error("{}", msg)
            self.close()
        return self.socket is not None

    def close(self):  # pylint: disable=arguments-differ
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _in_waiting(self):
        """Return _in_waiting."""
        in_waiting = "in_waiting" if hasattr(self.socket, "in_waiting") else "inWaiting"

        if in_waiting == "in_waiting":
            waitingbytes = getattr(self.socket, in_waiting)
        else:
            waitingbytes = getattr(self.socket, in_waiting)()
        return waitingbytes

    def send(self, request):
        """Send data on the underlying socket.

        If receive buffer still holds some data then flush it.

        Sleep if last send finished less than 3.5 character times ago.
        """
        super().send(request)
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            try:
                if waitingbytes := self._in_waiting():
                    result = self.socket.read(waitingbytes)
                    if self.state == ModbusTransactionState.RETRYING:
                        Log.debug(
                            "Sending available data in recv buffer {}", result, ":hex"
                        )
                        return result
                    Log.warning("Cleanup recv buffer before send: {}", result, ":hex")
            except NotImplementedError:
                pass
            if self.state != ModbusTransactionState.SENDING:
                Log.debug('New Transaction state "SENDING"')
                self.state = ModbusTransactionState.SENDING
            size = self.socket.write(request)
            return size
        return 0

    def _wait_for_data(self):
        """Wait for data."""
        size = 0
        more_data = False
        if (
            self.comm_params.timeout_connect is not None
            and self.comm_params.timeout_connect
        ):
            condition = partial(
                lambda start, timeout: (time.time() - start) <= timeout,
                timeout=self.comm_params.timeout_connect,
            )
        else:
            condition = partial(lambda dummy1, dummy2: True, dummy2=None)
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

    def recv(self, size):
        """Read data from the underlying descriptor."""
        super().recv(size)
        if not self.socket:
            raise ConnectionException(
                self.__str__()  # pylint: disable=unnecessary-dunder-call
            )
        if size is None:
            size = self._wait_for_data()
        if size > self._in_waiting():
            self._wait_for_data()
        result = self.socket.read(size)
        return result

    def is_socket_open(self):
        """Check if socket is open."""
        if self.socket:
            if hasattr(self.socket, "is_open"):
                return self.socket.is_open
            return self.socket.isOpen()
        return False

    def __str__(self):
        """Build a string representation of the connection."""
        return f"ModbusSerialClient({self.framer} baud[{self.comm_params.baudrate}])"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"framer={self.framer}, timeout={self.comm_params.timeout_connect}>"
        )
