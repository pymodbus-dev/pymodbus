"""Modbus client async serial communication."""
import asyncio
import time
from functools import partial

from pymodbus.client.base import ModbusBaseClient, ModbusClientProtocol
from pymodbus.client.serial_asyncio import create_serial_connection
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import ModbusFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.logging import Log
from pymodbus.utilities import ModbusTransactionState


try:
    import serial
except ImportError:
    pass


class AsyncModbusSerialClient(ModbusBaseClient):
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
            await client.close()
    """

    transport = None
    framer = None

    def __init__(
        self,
        port: str,
        framer: ModbusFramer = ModbusRtuFramer,
        baudrate: int = Defaults.Baudrate,
        bytesize: int = Defaults.Bytesize,
        parity: chr = Defaults.Parity,
        stopbits: int = Defaults.Stopbits,
        handle_local_echo: bool = Defaults.HandleLocalEcho,
        **kwargs: any,
    ) -> None:
        """Initialize Asyncio Modbus Serial Client."""
        self.protocol = None
        super().__init__(framer=framer, **kwargs)
        self.params.port = port
        self.params.baudrate = baudrate
        self.params.bytesize = bytesize
        self.params.parity = parity
        self.params.stopbits = stopbits
        self.params.handle_local_echo = handle_local_echo
        self.loop = None
        self._connected_event = asyncio.Event()

    async def close(self):  # pylint: disable=invalid-overridden-method
        """Stop connection."""

        # prevent reconnect:
        self.delay_ms = 0
        if self.connected:
            if self.protocol.transport:
                self.protocol.transport.close()
            if self.protocol:
                await self.protocol.close()
            await asyncio.sleep(0.1)

    def _create_protocol(self):
        """Create protocol."""
        protocol = ModbusClientProtocol(
            framer=self.params.framer, xframer=self.framer, timeout=self.params.timeout
        )
        protocol.factory = self
        return protocol

    @property
    def connected(self):
        """Connect internal."""
        return self._connected_event.is_set()

    async def connect(self):  # pylint: disable=invalid-overridden-method
        """Connect Async client."""
        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()

        Log.debug("Starting serial connection")
        try:
            await create_serial_connection(
                self.loop,
                self._create_protocol,
                self.params.port,
                baudrate=self.params.baudrate,
                bytesize=self.params.bytesize,
                stopbits=self.params.stopbits,
                parity=self.params.parity,
                timeout=self.params.timeout,
                **self.params.kwargs,
            )
            await self._connected_event.wait()
            Log.info("Connected to {}", self.params.port)
        except Exception as exc:  # pylint: disable=broad-except
            Log.warning("Failed to connect: {}", exc)
        return self.connected

    def protocol_made_connection(self, protocol):
        """Notify successful connection."""
        Log.info("Serial connected.")
        if not self.connected:
            self._connected_event.set()
            self.protocol = protocol
        else:
            Log.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection."""
        if self.connected:
            Log.info("Serial lost connection.")
            if protocol is not self.protocol:
                Log.error("Serial: protocol is not self.protocol.")

            self._connected_event.clear()
            if self.protocol is not None:
                del self.protocol
                self.protocol = None
            # if self.host:
            #     asyncio.asynchronous(self._reconnect())
        else:
            Log.error("Serial, lost_connection but not connected.")


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
    """

    state = ModbusTransactionState.IDLE
    inter_char_timeout = 0
    silent_interval = 0

    def __init__(
        self,
        port: str,
        framer: ModbusFramer = ModbusRtuFramer,
        baudrate: int = Defaults.Baudrate,
        bytesize: int = Defaults.Bytesize,
        parity: chr = Defaults.Parity,
        stopbits: int = Defaults.Stopbits,
        handle_local_echo: bool = Defaults.HandleLocalEcho,
        **kwargs: any,
    ) -> None:
        """Initialize Modbus Serial Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.port = port
        self.params.baudrate = baudrate
        self.params.bytesize = bytesize
        self.params.parity = parity
        self.params.stopbits = stopbits
        self.params.handle_local_echo = handle_local_echo
        self.socket = None

        self.last_frame_end = None
        if isinstance(self.framer, ModbusRtuFramer):
            if self.params.baudrate > 19200:
                self.silent_interval = 1.75 / 1000  # ms
            else:
                self._t0 = float((1 + 8 + 2)) / self.params.baudrate
                self.inter_char_timeout = 1.5 * self._t0
                self.silent_interval = 3.5 * self._t0
            self.silent_interval = round(self.silent_interval, 6)

    @property
    def connected(self):
        """Connect internal."""
        return self.connect()

    def connect(self):
        """Connect to the modbus serial server."""
        if self.socket:
            return True
        try:
            self.socket = serial.serial_for_url(
                self.params.port,
                timeout=self.params.timeout,
                bytesize=self.params.bytesize,
                stopbits=self.params.stopbits,
                baudrate=self.params.baudrate,
                parity=self.params.parity,
            )
            if isinstance(self.framer, ModbusRtuFramer):
                if self.params.strict:
                    self.socket.interCharTimeout = self.inter_char_timeout
                self.last_frame_end = None
        except serial.SerialException as msg:
            Log.error("{}", msg)
            self.close()
        return self.socket is not None

    def close(self):
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
        if self.params.timeout is not None and self.params.timeout:
            condition = partial(
                lambda start, timeout: (time.time() - start) <= timeout,
                timeout=self.params.timeout,
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
            time.sleep(0.01)
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
        elif size > self._in_waiting():
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
        return f"ModbusSerialClient({self.framer} baud[{self.params.baudrate}])"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"framer={self.framer}, timeout={self.params.timeout}>"
        )
