"""Base for all clients."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from typing import Any, Callable

from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.transaction import DictTransactionManager
from pymodbus.transport import CommParams, ModbusProtocol
from pymodbus.utilities import ModbusTransactionState


class ModbusBaseClient(ModbusClientMixin, ModbusProtocol):
    """**ModbusBaseClient**

    **Parameters common to all clients**:

    :param framer: (optional) Modbus Framer class.
    :param timeout: (optional) Timeout for a request, in seconds.
    :param retries: (optional) Max number of retries per request.
    :param retry_on_empty: (optional) Retry on empty response.
    :param close_comm_on_error: (optional) Close connection on error.
    :param strict: (optional) Strict timing, 1.5 character between requests.
    :param broadcast_enable: (optional) True to treat id 0 as broadcast address.
    :param reconnect_delay: (optional) Minimum delay in milliseconds before reconnecting.
    :param reconnect_delay_max: (optional) Maximum delay in milliseconds before reconnecting.
    :param on_reconnect_callback: (optional) Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: (optional) Do not resend request when retrying due to missing response.
    :param kwargs: (optional) Experimental parameters.

    .. tip::
        Common parameters and all external methods for all clients are documented here,
        and not repeated with each client.

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

        retries: int = None
        retry_on_empty: bool = None
        close_comm_on_error: bool = None
        strict: bool = None
        broadcast_enable: bool = None
        reconnect_delay: int = None

        source_address: tuple[str, int] = None

        server_hostname: str = None

    def __init__(  # pylint: disable=too-many-arguments
        self,
        framer: type[ModbusFramer] = None,
        timeout: float = 3,
        retries: int = 3,
        retry_on_empty: bool = False,
        close_comm_on_error: bool = False,
        strict: bool = True,
        broadcast_enable: bool = False,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        on_reconnect_callback: Callable[[], None] | None = None,
        no_resend_on_retry: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a client instance."""
        ModbusClientMixin.__init__(self)
        self.use_sync = kwargs.get("use_sync", False)
        setup_params = CommParams(
            comm_type=kwargs.get("CommType"),
            comm_name="comm",
            source_address=kwargs.get("source_address", ("0.0.0.0", 0)),
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
        )
        if not self.use_sync:
            ModbusProtocol.__init__(
                self,
                setup_params,
                False,
            )
        else:
            self.comm_params = setup_params
        self.params = self._params()
        self.params.retries = int(retries)
        self.params.retry_on_empty = bool(retry_on_empty)
        self.params.close_comm_on_error = bool(close_comm_on_error)
        self.params.strict = bool(strict)
        self.params.broadcast_enable = bool(broadcast_enable)
        self.params.reconnect_delay = int(reconnect_delay)
        self.reconnect_delay_max = int(reconnect_delay_max)
        self.on_reconnect_callback = on_reconnect_callback
        self.retry_on_empty: int = 0
        self.no_resend_on_retry = no_resend_on_retry
        self.slaves: list[int] = []

        # Common variables.
        self.framer = framer(ClientDecoder(), self)
        self.transaction = DictTransactionManager(
            self, retries=retries, retry_on_empty=retry_on_empty, **kwargs
        )
        self.reconnect_delay = self.params.reconnect_delay
        self.reconnect_delay_current = self.params.reconnect_delay
        self.use_udp = False
        self.state = ModbusTransactionState.IDLE
        self.last_frame_end: float = 0
        self.silent_interval: float = 0

    # ----------------------------------------------------------------------- #
    # Client external interface
    # ----------------------------------------------------------------------- #
    @property
    def connected(self):
        """Connect internal."""
        return True

    def register(self, custom_response_class: ModbusResponse) -> None:
        """Register a custom response class with the decoder (call **sync**).

        :param custom_response_class: (optional) Modbus response class.
        :raises MessageRegisterException: Check exception text.

        Use register() to add non-standard responses (like e.g. a login prompt) and
        have them interpreted automatically.
        """
        self.framer.decoder.register(custom_response_class)

    def close(self, reconnect=False) -> None:
        """Close connection."""
        if reconnect:
            self.connection_lost(asyncio.TimeoutError("Server not responding"))
        else:
            self.transport_close()

    def idle_time(self) -> float:
        """Time before initiating next transaction (call **sync**).

        Applications can call message functions without checking idle_time(),
        this is done automatically.
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def execute(self, request: ModbusRequest = None) -> ModbusResponse:
        """Execute request and get response (call **sync/async**).

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.
        """
        if self.use_sync:
            if not self.connect():
                raise ConnectionException(f"Failed to connect[{self!s}]")
            return self.transaction.execute(request)
        if not self.transport:
            raise ConnectionException(f"Not connected[{self!s}]")
        return self.async_execute(request)

    # ----------------------------------------------------------------------- #
    # Merged client methods
    # ----------------------------------------------------------------------- #
    async def async_execute(self, request=None):
        """Execute requests asynchronously."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)

        count = 0
        while count <= self.params.retries:
            if not count or not self.no_resend_on_retry:
                self.transport_send(packet)
            if self.params.broadcast_enable and not request.slave_id:
                resp = b"Broadcast write sent - no response expected"
                break
            try:
                req = self._build_response(request.transaction_id)
                resp = await asyncio.wait_for(
                    req, timeout=self.comm_params.timeout_connect
                )
                break
            except asyncio.exceptions.TimeoutError:
                count += 1
        if count > self.params.retries:
            self.close(reconnect=True)
            raise ModbusIOException(
                f"ERROR: No response received after {self.params.retries} retries"
            )

        return resp

    def callback_data(self, data: bytes, addr: tuple = None) -> int:
        """Handle received data

        returns number of bytes consumed
        """
        self.framer.processIncomingPacket(data, self._handle_response, slave=0)
        return len(data)

    def callback_disconnected(self, _reason: Exception) -> None:
        """Handle lost connection"""
        for tid in list(self.transaction):
            self.raise_future(
                self.transaction.getTransaction(tid),
                ConnectionException("Connection lost during request"),
            )

    async def connect(self):
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

    def _build_response(self, tid):
        """Return a deferred response for the current request."""
        my_future = asyncio.Future()
        if not self.transport:
            self.raise_future(my_future, ConnectionException("Client is not connected"))
        else:
            self.transaction.addTransaction(my_future, tid)
        return my_future

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
    def _get_address_family(cls, address):
        """Get the correct address family."""
        try:
            _ = socket.inet_pton(socket.AF_INET6, address)
        except OSError:  # not a valid ipv6 address
            return socket.AF_INET
        return socket.AF_INET6

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """

        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    async def __aenter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not await self.connect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    async def __aexit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return (
            f"{self.__class__.__name__} {self.comm_params.host}:{self.comm_params.port}"
        )
