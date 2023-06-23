"""Transport layer."""
# mypy: disable-error-code="name-defined"
# needed because asyncio.Server is not defined (to mypy) in v3.8.16
from __future__ import annotations

import asyncio
import dataclasses
import ssl
from enum import Enum
from typing import Any, Callable, Coroutine

from pymodbus.logging import Log
from pymodbus.transport.serial_asyncio import create_serial_connection


NULLMODEM_HOST = "__pymodbus_nullmodem"


class CommType(Enum):
    """Type of transport"""

    TCP = 1
    TLS = 2
    UDP = 3
    SERIAL = 4


@dataclasses.dataclass
class CommParams:
    """Parameter class."""

    # generic
    comm_name: str = None
    comm_type: CommType = None
    reconnect_delay: float = None
    reconnect_delay_max: float = None
    timeout_connect: float = None

    # tcp / tls / udp / serial
    host: str = None

    # tcp / tls / udp
    port: int = None

    # tls
    sslctx: ssl.SSLContext = None

    # serial
    baudrate: int = None
    bytesize: int = None
    parity: str = None
    stopbits: int = None

    @classmethod
    def generate_ssl(
        cls,
        is_server: bool,
        certfile: str = None,
        keyfile: str = None,
        password: str = None,
        sslctx: ssl.SSLContext = None,
    ) -> ssl.SSLContext:
        """Generate sslctx from cert/key/passwor

        MODBUS/TCP Security Protocol Specification demands TLSv2 at least
        """
        if sslctx:
            return sslctx
        new_sslctx = ssl.SSLContext(
            ssl.PROTOCOL_TLS_SERVER if is_server else ssl.PROTOCOL_TLS_CLIENT
        )
        new_sslctx.check_hostname = False
        new_sslctx.verify_mode = ssl.CERT_NONE
        new_sslctx.options |= ssl.OP_NO_TLSv1_1
        new_sslctx.options |= ssl.OP_NO_TLSv1
        new_sslctx.options |= ssl.OP_NO_SSLv3
        new_sslctx.options |= ssl.OP_NO_SSLv2
        if certfile:
            new_sslctx.load_cert_chain(
                certfile=certfile, keyfile=keyfile, password=password
            )
        return new_sslctx

    def copy(self):
        """Create a copy."""
        return dataclasses.replace(self)


class Transport(asyncio.BaseProtocol):
    """Protocol layer including transport.

    Contains pure transport methods needed to connect/listen, send/receive and close connections
    for unix socket, tcp, tls and serial communications.

    Contains high level methods like reconnect.

    The class is designed to take care of differences between the different transport mediums, and
    provide a neutral interface for the upper layers.
    """

    def __init__(
        self,
        params: CommParams,
        is_server: bool,
    ) -> None:
        """Initialize a transport instance.

        :param params: parameter dataclass
        :param is_server: true if object act as a server (listen allowed)
        :param callback_connected: Called when connection is established
        :param callback_disconnected: Called when connection is disconnected
        :param callback_data: Called when data is received
        """
        self.comm_params = params.copy()
        self.is_server = is_server

        self.reconnect_delay_current: float = 0.0
        self.listener: Transport = None
        self.transport: asyncio.BaseTransport | asyncio.Server = None
        self.loop: asyncio.AbstractEventLoop = None
        self.reconnect_task: asyncio.Task = None
        self.recv_buffer: bytes = b""
        self.call_create: Callable[[], Coroutine[Any, Any, Any]] = lambda: None
        self.active_connections: dict[str, Transport] = {}
        self.unique_id: str = str(id(self))

        # Transport specific setup
        if self.comm_params.host.startswith(NULLMODEM_HOST):
            self.call_create = self.create_nullmodem
            return
        if self.comm_params.comm_type == CommType.SERIAL:
            if self.comm_params.host.startswith("socket:") and is_server:
                parts = self.comm_params.host[9:].split(":")
                self.comm_params.host = parts[0]
                self.comm_params.port = int(parts[1])
                self.comm_params.comm_type = CommType.TCP
            else:
                self.call_create = lambda: create_serial_connection(
                    self.loop,
                    self.handle_new_connection,
                    self.comm_params.host,
                    baudrate=self.comm_params.baudrate,
                    bytesize=self.comm_params.bytesize,
                    parity=self.comm_params.parity,
                    stopbits=self.comm_params.stopbits,
                    timeout=self.comm_params.timeout_connect,
                )
                return
        if self.comm_params.comm_type == CommType.UDP:
            if is_server:
                self.call_create = lambda: self.loop.create_datagram_endpoint(
                    self.handle_new_connection,
                    local_addr=(self.comm_params.host, self.comm_params.port),
                )
            else:
                self.call_create = lambda: self.loop.create_datagram_endpoint(
                    self.handle_new_connection,
                    remote_addr=(self.comm_params.host, self.comm_params.port),
                )
            return
        # TLS and TCP
        if is_server:
            self.call_create = lambda: self.loop.create_server(
                self.handle_new_connection,
                self.comm_params.host,
                self.comm_params.port,
                ssl=self.comm_params.sslctx,
                reuse_address=True,
                start_serving=True,
            )
        else:
            self.call_create = lambda: self.loop.create_connection(
                self.handle_new_connection,
                self.comm_params.host,
                self.comm_params.port,
                ssl=self.comm_params.sslctx,
            )

    async def transport_connect(self) -> bool:
        """Handle generic connect and call on to specific transport connect."""
        Log.debug("Connecting {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        try:
            self.transport, _protocol = await asyncio.wait_for(
                self.call_create(),
                timeout=self.comm_params.timeout_connect,
            )
        except (
            asyncio.TimeoutError,
            OSError,
        ) as exc:
            Log.warning("Failed to connect {}", exc)
            self.transport_close(reconnect=True)
            return False
        return bool(self.transport)

    async def transport_listen(self) -> bool:
        """Handle generic listen and call on to specific transport listen."""
        Log.debug("Awaiting connections {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        try:
            self.transport = await self.call_create()
            if isinstance(self.transport, tuple):
                self.transport = self.transport[0]
        except OSError as exc:
            Log.warning("Failed to start server {}", exc)
            self.transport_close()
            return False
        return True

    # ---------------------------------- #
    # Transport asyncio standard methods #
    # ---------------------------------- #
    def connection_made(self, transport: asyncio.BaseTransport):
        """Call from asyncio, when a connection is made.

        :param transport: socket etc. representing the connection.
        """
        Log.debug("Connected to {}", self.comm_params.comm_name)
        self.transport = transport
        self.reset_delay()
        self.callback_connected()

    def connection_lost(self, reason: Exception):
        """Call from asyncio, when the connection is lost or closed.

        :param reason: None or an exception object
        """
        if not self.transport:
            return
        Log.debug("Connection lost {} due to {}", self.comm_params.comm_name, reason)
        self.transport_close()
        if not self.is_server:
            self.reconnect_task = asyncio.create_task(self.do_reconnect())
        self.callback_disconnected(reason)

    def data_received(self, data: bytes):
        """Call when some data is received.

        :param data: non-empty bytes object with incoming data.
        """
        Log.debug("recv: {}", data, ":hex")
        self.recv_buffer += data
        cut = self.callback_data(self.recv_buffer)
        self.recv_buffer = self.recv_buffer[cut:]

    def datagram_received(self, data: bytes, addr: tuple):
        """Receive datagram (UDP connections)."""
        Log.debug("recv: {} addr={}", data, ":hex", addr)
        self.recv_buffer += data
        cut = self.callback_data(self.recv_buffer, addr=addr)
        self.recv_buffer = self.recv_buffer[cut:]

    def eof_received(self):
        """Accept other end terminates connection."""
        Log.debug("-> eof_received")

    def error_received(self, exc):
        """Get error detected in UDP."""
        Log.debug("-> error_received {}", exc)
        raise RuntimeError(str(exc))

    # --------- #
    # callbacks #
    # --------- #
    def callback_connected(self) -> None:
        """Call when connection is succcesfull."""
        Log.debug("callback_connected called")

    def callback_disconnected(self, exc: Exception) -> None:
        """Call when connection is lost."""
        Log.debug("callback_disconnected called: {}", exc)

    def callback_data(self, data: bytes, addr: tuple = None) -> int:
        """Handle received data."""
        Log.debug("callback_data called: {} addr={}", data, ":hex", addr)
        return 0

    # ----------------------------------- #
    # Helper methods for external classes #
    # ----------------------------------- #
    def transport_send(self, data: bytes, addr: tuple = None) -> None:
        """Send request.

        :param data: non-empty bytes object with data to send.
        :param addr: optional addr, only used for UDP server.
        """
        Log.debug("send: {}", data, ":hex")
        if self.comm_params.comm_type == CommType.UDP:
            if addr:
                self.transport.sendto(data, addr=addr)  # type: ignore[union-attr]
            else:
                self.transport.sendto(data)  # type: ignore[union-attr]
        else:
            self.transport.write(data)  # type: ignore[union-attr]

    def transport_close(self, reconnect: bool = False) -> None:
        """Close connection.

        :param reconnect: (default false), try to reconnect
        """
        if self.transport:
            if hasattr(self.transport, "abort"):
                self.transport.abort()
            self.transport.close()
            self.transport = None
        if not reconnect and self.reconnect_task:
            self.reconnect_task.cancel()
            self.reconnect_task = None
            self.reconnect_delay_current = 0.0
            self.recv_buffer = b""
        if self.listener:
            self.listener.active_connections.pop(self.unique_id)
        elif self.is_server:
            for _key, value in self.active_connections.items():
                value.listener = None
                value.transport_close()
            self.active_connections = {}

    def reset_delay(self) -> None:
        """Reset wait time before next reconnect to minimal period."""
        self.reconnect_delay_current = self.comm_params.reconnect_delay

    def is_active(self) -> bool:
        """Return true if connected/listening."""
        return bool(self.transport)

    # ---------------- #
    # Internal methods #
    # ---------------- #
    async def create_nullmodem(self):
        """Bypass create_ and use null modem"""
        new_transport = NullModem(self.is_server, self)
        new_protocol = self.handle_new_connection()
        new_protocol.connection_made(new_transport)
        self.connection_made(self.transport)
        return new_transport, new_protocol

    def handle_new_connection(self):
        """Handle incoming connect."""
        if not self.is_server:
            return self

        new_transport = Transport(self.comm_params, True)
        new_transport.listener = self
        self.active_connections[new_transport.unique_id] = new_transport
        return new_transport

    async def do_reconnect(self):
        """Handle reconnect as a task."""
        try:
            self.reconnect_delay_current = self.comm_params.reconnect_delay
            while True:
                Log.debug(
                    "Wait {} {} ms before reconnecting.",
                    self.comm_params.comm_name,
                    self.reconnect_delay_current * 1000,
                )
                await asyncio.sleep(self.reconnect_delay_current)
                if await self.transport_connect():
                    break
                self.reconnect_delay_current = min(
                    2 * self.reconnect_delay_current,
                    self.comm_params.reconnect_delay_max,
                )
        except asyncio.CancelledError:
            pass
        self.reconnect_task = None

    # ----------------- #
    # The magic methods #
    # ----------------- #
    async def __aenter__(self):
        """Implement the client with async enter block."""
        return self

    async def __aexit__(self, _class, _value, _traceback) -> None:
        """Implement the client with async exit block."""
        self.transport_close()

    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_params.comm_name})"


class NullModem(asyncio.DatagramTransport, asyncio.WriteTransport):
    """Transport layer.

    Contains methods to act as a null modem between 2 objects.
    (Allowing tests to be shortcut without actual network calls)
    """

    listening: int = -1
    clients: list[NullModem] = []
    servers: list[NullModem] = []

    def __init__(self, is_server: bool, protocol: Transport):
        """Create half part of null modem"""
        asyncio.DatagramTransport.__init__(self)
        asyncio.WriteTransport.__init__(self)
        self.other: NullModem = None
        self.protocol = protocol
        self.serving: asyncio.Future = asyncio.Future()
        if is_server:
            self.conn_inx = len(self.servers)
            self.__class__.listening = self.conn_inx
            self.__class__.servers.append(self)
            return
        if self.listening < 0:
            raise OSError("Connect called before listen")
        self.conn_inx = self.listening
        self.__class__.listening = -1
        self.__class__.clients.append(self)
        self.other = self.servers[self.conn_inx]
        self.other.other = self

    # ---------------- #
    # external methods #
    # ---------------- #

    def close(self):
        """Close null modem"""
        if not self.serving.done():
            self.serving.set_result(True)
        if self.other:
            self.other.other = None
            self.other.protocol.connection_lost(None)
            self.other = None
            self.protocol.connection_lost(None)

    def sendto(self, data: bytes, _addr: Any = None):
        """Send datagrame"""
        return self.write(data)

    def write(self, data: bytes):
        """Send data"""
        self.other.protocol.data_received(data)

    async def serve_forever(self):
        """Serve forever"""
        await self.serving

    # ---------------- #
    # Abstract methods #
    # ---------------- #
    def abort(self) -> None:
        """Abort connection."""

    def can_write_eof(self) -> bool:
        """Allow to write eof"""
        return True

    def get_write_buffer_size(self) -> int:
        """Set write limit."""
        return 1024

    def get_write_buffer_limits(self) -> tuple[int, int]:
        """Set flush limits"""
        return (1, 1024)

    def set_write_buffer_limits(self, high: int = None, low: int = None) -> None:
        """Set flush limits"""

    def write_eof(self) -> None:
        """Write eof"""

    def get_protocol(self) -> Transport:
        """Return current protocol."""
        return None

    def set_protocol(self, protocol: asyncio.BaseProtocol) -> None:
        """Set current protocol."""

    def is_closing(self) -> bool:
        """Return true if closing"""
        return False
