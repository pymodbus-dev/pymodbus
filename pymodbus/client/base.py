"""Base for all clients."""
from __future__ import annotations

import asyncio
import socket
from abc import abstractmethod
from collections.abc import Awaitable, Callable

from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.client.modbusclientprotocol import ModbusClientProtocol
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerBase, FramerType
from pymodbus.logging import Log
from pymodbus.pdu import DecodePDU, ExceptionResponse, ModbusPDU
from pymodbus.transaction import SyncModbusTransactionManager
from pymodbus.transport import CommParams
from pymodbus.utilities import ModbusTransactionState


class ModbusBaseClient(ModbusClientMixin[Awaitable[ModbusPDU]]):
    """**ModbusBaseClient**.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerType,
        retries: int,
        on_connect_callback: Callable[[bool], None] | None,
        comm_params: CommParams | None = None,
    ) -> None:
        """Initialize a client instance.

        :meta private:
        """
        ModbusClientMixin.__init__(self)  # type: ignore[arg-type]
        if comm_params:
            self.comm_params = comm_params
        self.retries = retries
        self.ctx = ModbusClientProtocol(
            framer,
            self.comm_params,
            on_connect_callback,
        )

        # Common variables.
        self.use_udp = False
        self.state = ModbusTransactionState.IDLE
        self.last_frame_end: float | None = 0
        self.silent_interval: float = 0
        self._lock = asyncio.Lock()
        self.accept_no_response_limit = 3
        self.count_no_responses = 0

    @property
    def connected(self) -> bool:
        """Return state of connection."""
        return self.ctx.is_active()

    async def connect(self) -> bool:
        """Call transport connect."""
        self.ctx.reset_delay()
        Log.debug(
            "Connecting to {}:{}.",
            self.ctx.comm_params.host,
            self.ctx.comm_params.port,
        )
        return await self.ctx.connect()

    def register(self, custom_response_class: type[ModbusPDU]) -> None:
        """Register a custom response class with the decoder (call **sync**).

        :param custom_response_class: (optional) Modbus response class.
        :raises MessageRegisterException: Check exception text.

        Use register() to add non-standard responses (like e.g. a login prompt) and
        have them interpreted automatically.
        """
        self.ctx.framer.decoder.register(custom_response_class)

    def close(self) -> None:
        """Close connection."""
        self.ctx.close()

    def execute(self, no_response_expected: bool, request: ModbusPDU):
        """Execute request and get response (call **sync/async**).

        :meta private:
        """
        if not self.ctx.transport:
            raise ConnectionException(f"Not connected[{self!s}]")
        return self.async_execute(no_response_expected, request)

    async def async_execute(self, no_response_expected: bool, request) -> ModbusPDU | None:
        """Execute requests asynchronously.

        :meta private:
        """
        request.transaction_id = self.ctx.transaction.getNextTID()
        packet = self.ctx.framer.buildFrame(request)

        count = 0
        while count <= self.retries:
            async with self._lock:
                req = self.build_response(request)
                self.ctx.send(packet)
                if no_response_expected:
                    resp = None
                    break
                try:
                    resp = await asyncio.wait_for(
                        req, timeout=self.ctx.comm_params.timeout_connect
                    )
                    break
                except asyncio.exceptions.TimeoutError:
                    count += 1
        if count > self.retries:
            if self.count_no_responses >= self.accept_no_response_limit:
                self.ctx.connection_lost(asyncio.TimeoutError("Server not responding"))
                raise ModbusIOException(
                    f"ERROR: No response received of the last {self.accept_no_response_limit} request, CLOSING CONNECTION."
                )
            self.count_no_responses += 1
            Log.error(f"No response received after {self.retries} retries, continue with next request")
            return ExceptionResponse(request.function_code)

        self.count_no_responses = 0
        return resp

    def build_response(self, request: ModbusPDU):
        """Return a deferred response for the current request.

        :meta private:
        """
        my_future: asyncio.Future = asyncio.Future()
        request.fut = my_future
        if not self.ctx.transport:
            if not my_future.done():
                my_future.set_exception(ConnectionException("Client is not connected"))
        else:
            self.ctx.transaction.addTransaction(request)
        return my_future

    async def __aenter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        await self.connect()
        return self

    async def __aexit__(self, klass, value, traceback):
        """Implement the client with aexit block."""
        self.close()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.ctx.comm_params.host}:{self.ctx.comm_params.port}"
        )


class ModbusBaseSyncClient(ModbusClientMixin[ModbusPDU]):
    """**ModbusBaseClient**.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerType,
        retries: int,
        comm_params: CommParams | None = None,
    ) -> None:
        """Initialize a client instance.

        :meta private:
        """
        ModbusClientMixin.__init__(self)  # type: ignore[arg-type]
        if comm_params:
            self.comm_params = comm_params
        self.retries = retries
        self.slaves: list[int] = []

        # Common variables.
        self.framer: FramerBase = (FRAMER_NAME_TO_CLASS[framer])(DecodePDU(False))
        self.transaction = SyncModbusTransactionManager(
            self,
            self.retries,
        )
        self.reconnect_delay_current = self.comm_params.reconnect_delay or 0
        self.use_udp = False
        self.state = ModbusTransactionState.IDLE
        self.last_frame_end: float | None = 0
        self.silent_interval: float = 0
        self.transport = None

    # ----------------------------------------------------------------------- #
    # Client external interface
    # ----------------------------------------------------------------------- #
    def register(self, custom_response_class: type[ModbusPDU]) -> None:
        """Register a custom response class with the decoder.

        :param custom_response_class: (optional) Modbus response class.
        :raises MessageRegisterException: Check exception text.

        Use register() to add non-standard responses (like e.g. a login prompt) and
        have them interpreted automatically.
        """
        self.framer.decoder.register(custom_response_class)

    def idle_time(self) -> float:
        """Time before initiating next transaction (call **sync**).

        Applications can call message functions without checking idle_time(),
        this is done automatically.
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def execute(self, no_response_expected: bool, request: ModbusPDU) -> ModbusPDU:
        """Execute request and get response (call **sync/async**).

        :param no_response_expected: The client will not expect a response to the request
        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.

        :meta private:
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self!s}]")
        return self.transaction.execute(no_response_expected, request)

    # ----------------------------------------------------------------------- #
    # Internal methods
    # ----------------------------------------------------------------------- #
    def _start_send(self):
        """Send request.

        :meta private:
        """
        if self.state != ModbusTransactionState.RETRYING:
            Log.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING

    @abstractmethod
    def send(self, request: bytes) -> int:
        """Send request.

        :meta private:
        """

    @abstractmethod
    def recv(self, size: int | None) -> bytes:
        """Receive data.

        :meta private:
        """

    @classmethod
    def get_address_family(cls, address):
        """Get the correct address family.

        :meta private:
        """
        try:
            _ = socket.inet_pton(socket.AF_INET6, address)
        except OSError:  # not a valid ipv6 address
            return socket.AF_INET
        return socket.AF_INET6

    def connect(self) -> bool:  # type: ignore[empty-body]
        """Connect to other end, overwritten."""

    def close(self):
        """Close connection, overwritten."""

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        self.connect()
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
