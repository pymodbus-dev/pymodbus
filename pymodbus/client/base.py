"""Base for all clients."""
from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass

from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException, NotImplementedException
from pymodbus.factory import ClientDecoder
from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.transaction import DictTransactionManager
from pymodbus.utilities import ModbusTransactionState


class ModbusBaseClient(ModbusClientMixin):
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
    :param kwargs: (optional) Experimental parameters.

    .. tip::
        Common parameters and all external methods for all clients are documented here,
        and not repeated with each client.

    .. tip::
        **delay_ms** doubles automatically with each unsuccessful connect, from
        **reconnect_delay** to **reconnect_delay_max**.
        Set `reconnect_delay=0` to avoid automatic reconnection.

    :mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`,
    unless you want to make a custom client.

    Custom client class **must** inherit :mod:`ModbusBaseClient`, example::

        from pymodbus.client import ModbusBaseClient

        class myOwnClient(ModbusBaseClient):

            def __init__(self, **kwargs):
                super().__init__(kwargs)

        def run():
            client = myOwnClient(...)
            client.connect()
            rr = client.read_coils(0x01)
            client.close()

    **Application methods, common to all clients**:
    """

    state = ModbusTransactionState.IDLE
    last_frame_end = 0
    silent_interval = 0

    @dataclass
    class _params:  # pylint: disable=too-many-instance-attributes
        """Parameter class."""

        host: str = None
        port: str | int = None
        framer: ModbusFramer = None
        timeout: float = None
        retries: int = None
        retry_on_empty: bool = None
        close_comm_on_error: bool = None
        strict: bool = None
        broadcast_enable: bool = None
        kwargs: dict = None
        reconnect_delay: int = None
        reconnect_delay_max: int = None

        baudrate: int = None
        bytesize: int = None
        parity: str = None
        stopbits: int = None
        handle_local_echo: bool = None

        source_address: str = None

        sslctx: str = None
        certfile: str = None
        keyfile: str = None
        password: str = None
        server_hostname: str = None

    def __init__(
        self,
        framer: str = None,
        timeout: str | float = Defaults.Timeout,
        retries: str | int = Defaults.Retries,
        retry_on_empty: bool = Defaults.RetryOnEmpty,
        close_comm_on_error: bool = Defaults.CloseCommOnError,
        strict: bool = Defaults.Strict,
        broadcast_enable: bool = Defaults.BroadcastEnable,
        reconnect_delay: int = Defaults.ReconnectDelay,
        reconnect_delay_max: int = Defaults.ReconnectDelayMax,
        **kwargs: any,
    ) -> None:
        """Initialize a client instance."""
        self.params = self._params()
        self.params.framer = framer
        self.params.timeout = float(timeout)
        self.params.retries = int(retries)
        self.params.retry_on_empty = bool(retry_on_empty)
        self.params.close_comm_on_error = bool(close_comm_on_error)
        self.params.strict = bool(strict)
        self.params.broadcast_enable = bool(broadcast_enable)
        self.params.reconnect_delay = int(reconnect_delay)
        self.params.reconnect_delay_max = int(reconnect_delay_max)
        self.params.kwargs = kwargs

        # Common variables.
        if xframer := kwargs.get("xframer", None):
            self.framer = xframer
        else:
            self.framer = self.params.framer(ClientDecoder(), self)
        self.transaction = DictTransactionManager(self, **kwargs)
        self.delay_ms = self.params.reconnect_delay
        self.use_protocol = hasattr(self, "protocol")

        # Initialize  mixin
        super().__init__()

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

    def connect(self) -> None:
        """Connect to the modbus remote host (call **sync/async**).

        :raises ModbusException: Different exceptions, check exception text.

        **Remark** Retries are handled automatically after first successful connect.
        """
        raise NotImplementedException

    def is_socket_open(self) -> bool:
        """Return whether socket/serial is open or not (call **sync**)."""
        raise NotImplementedException

    def idle_time(self) -> int:
        """Time before initiating next transaction (call **sync**).

        Applications can call message functions without checking idle_time(),
        this is done automatically.
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def reset_delay(self) -> None:
        """Reset wait time before next reconnect to minimal period (call **sync**)."""
        self.delay_ms = self.params.reconnect_delay

    def execute(self, request: ModbusRequest = None) -> ModbusResponse:
        """Execute request and get response (call **sync/async**).

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException: Check exception text.
        """
        if self.use_protocol:
            if not self.protocol:
                raise ConnectionException(f"Not connected[{str(self)}]")
            return self.protocol.execute(request)
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{str(self)}]")
        return self.transaction.execute(request)

    def close(self) -> None:
        """Close the underlying socket connection (call **sync/async**)."""
        raise NotImplementedException

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
        except socket.error:  # not a valid ipv6 address
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
        await self.close()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"{self.__class__.__name__} {self.params.host}:{self.params.port}"


class ModbusClientProtocol(
    ModbusBaseClient,
    asyncio.Protocol,
    asyncio.DatagramProtocol,
):
    """Asyncio specific implementation of asynchronous modbus client protocol."""

    #: Factory that created this instance.
    factory = None
    transport = None

    def __init__(
        self, host="127.0.0.1", port=502, source_address=None, use_udp=False, **kwargs
    ):
        """Initialize a Modbus TCP/UDP asynchronous client"""
        super().__init__(**kwargs)
        self.use_udp = use_udp
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address or ("", 0)

        self._connected = False

    def datagram_received(self, data, addr):
        """Receive datagram."""
        self._data_received(data)

    async def execute(self, request=None):  # pylint: disable=invalid-overridden-method
        """Execute requests asynchronously."""
        req = self._execute(request)
        if self.params.broadcast_enable and not request.unit_id:
            resp = b"Broadcast write sent - no response expected"
        else:
            resp = await asyncio.wait_for(req, timeout=self.params.timeout)
        return resp

    def connection_made(self, transport):
        """Call when a connection is made.

        The transport argument is the transport representing the connection.
        """
        self.transport = transport
        self._connection_made()

        if self.factory:
            self.factory.protocol_made_connection(  # pylint: disable=no-member,useless-suppression
                self
            )

    async def close(self):  # pylint: disable=invalid-overridden-method
        """Close connection."""
        if self.transport:
            self.transport.close()
            while self.transport is not None:
                await asyncio.sleep(0.1)
        self._connected = False

    def connection_lost(self, reason):
        """Call when the connection is lost or closed.

        The argument is either an exception object or None
        """
        self.transport = None
        self._connection_lost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(  # pylint: disable=no-member,useless-suppression
                self
            )

    def data_received(self, data):
        """Call when some data is received.

        data is a non-empty bytes object containing the incoming data.
        """
        self._data_received(data)

    def create_future(self):
        """Help function to create asyncio Future object."""
        return asyncio.Future()

    def resolve_future(self, my_future, result):
        """Resolve the completed future and sets the result."""
        if not my_future.done():
            my_future.set_result(result)

    def raise_future(self, my_future, exc):
        """Set exception of a future if not done."""
        if not my_future.done():
            my_future.set_exception(exc)

    def _connection_made(self):
        """Call upon a successful client connection."""
        Log.debug("Client connected to modbus server")
        self._connected = True

    def _connection_lost(self, reason):
        """Call upon a client disconnect."""
        Log.debug("Client disconnected from modbus server: {}", reason)
        self._connected = False
        for tid in list(self.transaction):
            self.raise_future(
                self.transaction.getTransaction(tid),
                ConnectionException("Connection lost during request"),
            )

    @property
    def connected(self):
        """Return connection status."""
        return self._connected

    def write_transport(self, packet):
        """Write transport."""
        if self.use_udp:
            return self.transport.sendto(packet)
        return self.transport.write(packet)

    def _execute(self, request, **kwargs):  # pylint: disable=unused-argument
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        Log.debug("send: {}", packet, ":hex")
        self.write_transport(packet)
        return self._build_response(request.transaction_id)

    def _data_received(self, data):
        """Get response, check for valid message, decode result."""
        Log.debug("recv: {}", data, ":hex")
        self.framer.processIncomingPacket(data, self._handle_response, unit=0)

    def _handle_response(self, reply, **kwargs):  # pylint: disable=unused-argument
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                self.resolve_future(handler, reply)
            else:
                Log.debug("Unrequested message: {}", reply, ":str")

    def _build_response(self, tid):
        """Return a deferred response for the current request."""
        my_future = self.create_future()
        if not self._connected:
            self.raise_future(my_future, ConnectionException("Client is not connected"))
        else:
            self.transaction.addTransaction(my_future, tid)
        return my_future
