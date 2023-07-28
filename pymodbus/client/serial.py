"""Modbus client async serial communication."""
import asyncio
import time
from contextlib import suppress
from functools import partial
from typing import Any, Type

from pymodbus.client.base import ModbusBaseClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import ModbusFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.logging import Log
from pymodbus.transport import CommType
from pymodbus.utilities import ModbusTransactionState


with suppress(ImportError):
    import serial


class AsyncModbusSerialClient(ModbusBaseClient, asyncio.Protocol):
    """**AsyncModbusSerialClient**.

    :param port: Serial port used for communication.
    :param framer: (optional) Framer class.
    :param baudrate: (optional) Bits per second.
    :param bytesize: (optional) Number of bits per byte 7-8.
    :param parity: (optional) 'E'ven, 'O'dd or 'N'one
    :param stopbits: (optional) Number of stop bits 0-2¡.
    :param handle_local_echo: (optional) Discard local echo from dongle.
    :param kwargs: (optional) Experimental parameters

    The serial communication is RS-485 based, and usually used with a usb RS485 dongle.

    Example::

        from pymodbus.client import AsyncModbusSerialClient

        async def run():
            client = AsyncModbusSerialClient("dev/serial0")

            await client.connect()
            ...
            client.close()
    """

    def __init__(
        self,
        port: str,
        framer: Type[ModbusFramer] = ModbusRtuFramer,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus Serial Client."""
        asyncio.Protocol.__init__(self)
        ModbusBaseClient.__init__(
            self,
            framer=framer,
            CommType=CommType.SERIAL,
            host=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            **kwargs,
        )

    @property
    def connected(self):
        """Connect internal."""
        return self.is_active()

    async def connect(self) -> bool:
        """Connect Async client."""
        # if reconnect_delay_current was set to 0 by close(), we need to set it back again
        # so this instance will work
        self.reset_delay()

        # force reconnect if required:
        Log.debug("Connecting to {}.", self.comm_params.host)
        return await self.transport_connect()


class ModbusSerialClient(ModbusBaseClient):
    """**ModbusSerialClient**.

    :param port: Serial port used for communication.
    :param framer: (optional) Framer class.
    :param baudrate: (optional) Bits per second.
    :param bytesize: (optional) Number of bits per byte 7-8.
    :param parity: (optional) 'E'ven, 'O'dd or 'N'one
    :param stopbits: (optional) Number of stop bits 0-2¡.
    :param handle_local_echo: (optional) Discard local echo from dongle.
    :param kwargs: (optional) Experimental parameters

    The serial communication is RS-485 based, and usually used with a usb RS485 dongle.

    Example::

        from pymodbus.client import ModbusSerialClient

        def run():
            client = ModbusSerialClient("dev/serial0")

            client.connect()
            ...
            client.close()


    Remark: There are no automatic reconnect as with AsyncModbusSerialClient
    """

    state = ModbusTransactionState.IDLE
    inter_char_timeout: float = 0
    silent_interval: float = 0

    def __init__(
        self,
        port: str,
        framer: Type[ModbusFramer] = ModbusRtuFramer,
        baudrate: int = 19200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus Serial Client."""
        self.transport = None
        kwargs["use_sync"] = True
        ModbusBaseClient.__init__(
            self,
            framer=framer,
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

        self._t0 = float(1 + 8 + 2) / self.comm_params.baudrate

        """
        The minimum delay is 0.01s and the maximum can be set to 0.05s.
        Setting too large a setting affects efficiency.
        """
        self._recv_interval = (
            (round((100 * self._t0), 2) + 0.01)
            if (round((100 * self._t0), 2) + 0.01) < 0.05
            else 0.05
        )

        if self.comm_params.baudrate > 19200:
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
            if isinstance(self.framer, ModbusRtuFramer):
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
