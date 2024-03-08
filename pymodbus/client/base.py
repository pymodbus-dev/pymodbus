"""Base for all clients."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Type, cast

from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import FRAMER_NAME_TO_CLASS, Framer, ModbusFramer
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.transaction import ModbusTransactionManager
from pymodbus.transport import CommParams, ModbusProtocol
from pymodbus.utilities import ModbusTransactionState


class ModbusBaseClient(ModbusClientMixin[Awaitable[ModbusResponse]], ModbusProtocol):
    """**ModbusBaseClient**.

    Fixed parameters:

    :param framer: Framer enum name

    Optional parameters:

    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    .. tip::
        **reconnect_delay** doubles automatically with each unsuccessful connect, from
        **reconnect_delay** to **reconnect_delay_max**.
        Set `reconnect_delay=0` to avoid automatic reconnection.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`.

    **Application methods, common to all clients**:
    """

    def __init__(
        self,
        framer: Framer,
        timeout: float = 3,
        retries: int = 3,
        retry_on_empty: bool = False,
        broadcast_enable: bool = False,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        on_reconnect_callback: Callable[[], None] | None = None,
        no_resend_on_retry: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a client instance."""
        ModbusClientMixin.__init__(self)  # type: ignore[arg-type]
        ModbusProtocol.__init__(
            self,
            CommParams(
                comm_type=kwargs.get("CommType"),
                comm_name="comm",
                source_address=kwargs.get("source_address", None),
                reconnect_delay=reconnect_delay,
                reconnect_delay_max=reconnect_delay_max,
                timeout_connect=timeout,
                host=kwargs.get("host", None),
                port=kwargs.get("port", 0),
                sslctx=kwargs.get("sslctx", None),
                baudrate=kwargs.get("baudrate", None),
                bytesize=kwargs.get("bytesize", None),
                parity=kwargs.get("parity", None),
                stopbits=kwargs.get("stopbits", None),
                handle_local_echo=kwargs.get("handle_local_echo", False),
            ),
            False,
        )
        self.on_reconnect_callback = on_reconnect_callback
        self.retry_on_empty: int = 0
        self.no_resend_on_retry = no_resend_on_retry
        self.slaves: list[int] = []
        self.retries: int = retries
        self.broadcast_enable = broadcast_enable

        # Common variables.
        self.framer = FRAMER_NAME_TO_CLASS.get(
            framer, cast(Type[ModbusFramer], framer)
        )(ClientDecoder(), self)
        self.transaction = ModbusTransactionManager(
            self, retries=retries, retry_on_empty=retry_on_empty, **kwargs
        )
        self.use_udp = False
        self.state = ModbusTransactionState.IDLE
        self.last_frame_end: float | None = 0
        self.silent_interval: float = 0

    # ----------------------------------------------------------------------- #
    # Client external interface
    # ----------------------------------------------------------------------- #
    @property
    def connected(self) -> bool:
        """Return state of connection."""
        return self.is_active()

    async def base_connect(self) -> bool:
        """Call transport connect."""
        return await super().connect()


    def register(self, custom_response_class: ModbusResponse) -> None:
        """Register a custom response class with the decoder (call **sync**).

        :param custom_response_class: (optional) Modbus response class.
        :raises MessageRegisterException: Check exception text.

        Use register() to add non-standard responses (like e.g. a login prompt) and
        have them interpreted automatically.
        """
        self.framer.decoder.register(custom_response_class)

    def close(self, reconnect: bool = False) -> None:
        """Close connection."""
        if reconnect:
            self.connection_lost(asyncio.TimeoutError("Server not responding"))
        else:
            super().close()

    def idle_time(self) -> float:
        """Time before initiating next transaction (call **sync**).

        Applications can call message functions without checking idle_time(),
        this is done automatically.
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def execute(self, request: ModbusRequest | None = None):
        """Execute request and get response (call **sync/async**).

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.
        """
        if not self.transport:
            raise ConnectionException(f"Not connected[{self!s}]")
        return self.async_execute(request)

    # ----------------------------------------------------------------------- #
    # Merged client methods
    # ----------------------------------------------------------------------- #
    async def async_execute(self, request) -> ModbusResponse:
        """Execute requests asynchronously."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)

        count = 0
        while count <= self.retries:
            req = self.build_response(request.transaction_id)
            if not count or not self.no_resend_on_retry:
                self.send(packet)
            if self.broadcast_enable and not request.slave_id:
                resp = None
                break
            try:
                resp = await asyncio.wait_for(
                    req, timeout=self.comm_params.timeout_connect
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

    def callback_new_connection(self):
        """Call when listener receive new connection request."""

    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""

    def callback_disconnected(self, exc: Exception | None) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle received data.

        returns number of bytes consumed
        """
        self.framer.processIncomingPacket(data, self._handle_response, slave=0)
        return len(data)

    async def connect(self) -> bool:  # type: ignore[empty-body]
        """Connect to the modbus remote host."""

    def raise_future(self, my_future, exc):
        """Set exception of a future if not done."""
        if not my_future.done():
            my_future.set_exception(exc)

    def _handle_response(self, reply, **_kwargs):
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                if not handler.done():
                    handler.set_result(reply)
            else:
                Log.debug("Unrequested message: {}", reply, ":str")

    def build_response(self, tid):
        """Return a deferred response for the current request."""
        my_future: asyncio.Future = asyncio.Future()
        if not self.transport:
            self.raise_future(my_future, ConnectionException("Client is not connected"))
        else:
            self.transaction.addTransaction(my_future, tid)
        return my_future

    # ----------------------------------------------------------------------- #
    # Internal methods
    # ----------------------------------------------------------------------- #
    def recv(self, size):
        """Receive data.

        :meta private:
        """

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
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
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )


class ModbusBaseSyncClient(ModbusClientMixin[ModbusResponse]):
    """**ModbusBaseClient**.

    Fixed parameters:

    :param framer: Framer enum name

    Optional parameters:

    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    .. tip::
        **reconnect_delay** doubles automatically with each unsuccessful connect, from
        **reconnect_delay** to **reconnect_delay_max**.
        Set `reconnect_delay=0` to avoid automatic reconnection.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`.

    **Application methods, common to all clients**:
    """

    @dataclass
    class _params:
        """Parameter class."""

        retries: int | None = None
        retry_on_empty: bool | None = None
        broadcast_enable: bool | None = None
        reconnect_delay: int | None = None
        source_address: tuple[str, int] | None = None

    def __init__(
        self,
        framer: Framer,
        timeout: float = 3,
        retries: int = 3,
        retry_on_empty: bool = False,
        broadcast_enable: bool = False,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300.0,
        on_reconnect_callback: Callable[[], None] | None = None,
        no_resend_on_retry: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a client instance."""
        ModbusClientMixin.__init__(self)  # type: ignore[arg-type]
        self.comm_params = CommParams(
            comm_type=kwargs.get("CommType"),
            comm_name="comm",
            source_address=kwargs.get("source_address", None),
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
            host=kwargs.get("host", None),
            port=kwargs.get("port", 0),
            sslctx=kwargs.get("sslctx", None),
            baudrate=kwargs.get("baudrate", None),
            bytesize=kwargs.get("bytesize", None),
            parity=kwargs.get("parity", None),
            stopbits=kwargs.get("stopbits", None),
            handle_local_echo=kwargs.get("handle_local_echo", False),
            on_reconnect_callback=on_reconnect_callback,
        )
        self.params = self._params()
        self.params.retries = int(retries)
        self.params.retry_on_empty = bool(retry_on_empty)
        self.params.broadcast_enable = bool(broadcast_enable)
        self.retry_on_empty: int = 0
        self.no_resend_on_retry = no_resend_on_retry
        self.slaves: list[int] = []

        # Common variables.
        self.framer = FRAMER_NAME_TO_CLASS.get(
            framer, cast(Type[ModbusFramer], framer)
        )(ClientDecoder(), self)
        self.transaction = ModbusTransactionManager(
            self, retries=retries, retry_on_empty=retry_on_empty, **kwargs
        )
        self.reconnect_delay_current = self.params.reconnect_delay or 0
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

    def execute(self, request: ModbusRequest | None = None) -> ModbusResponse:
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
    def send(self, request):
        """Send request.

        :meta private:
        """
        if self.state != ModbusTransactionState.RETRYING:
            Log.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING
        return request

    def recv(self, size):
        """Receive data.

        :meta private:
        """
        return size

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
