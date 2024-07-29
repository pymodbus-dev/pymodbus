"""Base for all clients."""
from __future__ import annotations

import asyncio
import socket
from abc import abstractmethod
from collections.abc import Awaitable, Callable
from typing import cast

from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.client.modbusclientprotocol import ModbusClientProtocol
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import FRAMER_NAME_TO_CLASS, FramerType, ModbusFramer
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.transaction import SyncModbusTransactionManager
from pymodbus.transport import CommParams
from pymodbus.utilities import ModbusTransactionState


class ModbusBaseClient(ModbusClientMixin[Awaitable[ModbusResponse]]):
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
        """Initialize a client instance."""
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

    def register(self, custom_response_class: ModbusResponse) -> None:
        """Register a custom response class with the decoder (call **sync**).

        :param custom_response_class: (optional) Modbus response class.
        :raises MessageRegisterException: Check exception text.

        Use register() to add non-standard responses (like e.g. a login prompt) and
        have them interpreted automatically.
        """
        self.ctx.framer.decoder.register(custom_response_class)

    def close(self, reconnect: bool = False) -> None:
        """Close connection."""
        if reconnect:
            self.ctx.connection_lost(asyncio.TimeoutError("Server not responding"))
        else:
            self.ctx.close()

    def idle_time(self) -> float:
        """Time before initiating next transaction (call **sync**).

        Applications can call message functions without checking idle_time(),
        this is done automatically.
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def execute(self, request: ModbusRequest):
        """Execute request and get response (call **sync/async**).

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.
        """
        if not self.ctx.transport:
            raise ConnectionException(f"Not connected[{self!s}]")
        return self.async_execute(request)

    async def async_execute(self, request) -> ModbusResponse:
        """Execute requests asynchronously."""
        request.transaction_id = self.ctx.transaction.getNextTID()
        packet = self.ctx.framer.buildPacket(request)

        count = 0
        while count <= self.retries:
            async with self._lock:
                req = self.build_response(request)
                self.ctx.framer.resetFrame()
                self.ctx.send(packet)
                if not request.slave_id:
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
            self.close(reconnect=True)
            raise ModbusIOException(
                f"ERROR: No response received after {self.retries} retries"
            )

        return resp  # type: ignore[return-value]

    def build_response(self, request: ModbusRequest):
        """Return a deferred response for the current request."""
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


class ModbusBaseSyncClient(ModbusClientMixin[ModbusResponse]):
    """**ModbusBaseClient**.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`.
    """

    def __init__(
        self,
        framer: FramerType,
        retries: int,
        comm_params: CommParams | None = None,
    ) -> None:
        """Initialize a client instance."""
        ModbusClientMixin.__init__(self)  # type: ignore[arg-type]
        if comm_params:
            self.comm_params = comm_params
        self.retries = retries
        self.slaves: list[int] = []

        # Common variables.
        self.framer: ModbusFramer = FRAMER_NAME_TO_CLASS.get(
            framer, cast(type[ModbusFramer], framer)
        )(ClientDecoder(), self)
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
    def register(self, custom_response_class: ModbusResponse) -> None:
        """Register a custom response class with the decoder (call **sync**).

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

    def execute(self, request: ModbusRequest) -> ModbusResponse:
        """Execute request and get response (call **sync/async**).

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self!s}]")
        return self.transaction.execute(request)

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
        """Get the correct address family."""
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
