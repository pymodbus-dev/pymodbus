"""Base for all transport types."""
# mypy: disable-error-code="name-defined"
# needed because asyncio.Server is not defined (to mypy) in v3.8.16
from __future__ import annotations

import asyncio
import ssl
import sys
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Callable, Coroutine

from pymodbus.logging import Log
from pymodbus.transport.serial_asyncio import create_serial_connection


class Transport:
    """Transport layer.

    Contains pure transport methods needed to connect/listen, send/receive and close connections
    for unix socket, tcp, tls and serial communications.

    Contains high level methods like reconnect.

    This class is not available in the pymodbus API, and should not be referenced in Applications
    nor in the pymodbus documentation.

    The class is designed to be an object in the message level class.
    """

    @dataclass
    class CommParamsClass:
        """Parameter class."""

        # generic
        done: bool = False
        comm_name: str = None
        reconnect_delay: float = None
        reconnect_delay_max: float = None
        timeout_connect: float = None

        # tcp / tls / udp / serial
        host: str = None

        # tcp / tls / udp
        port: int = None

        # tls
        ssl: ssl.SSLContext = None
        server_hostname: str = None

        # serial
        baudrate: int = None
        bytesize: int = None
        parity: str = None
        stopbits: int = None

        def check_done(self):
            """Check if already setup"""
            if self.done:
                raise RuntimeError("Already setup!")
            self.done = True

    def __init__(
        self,
        comm_name: str,
        reconnect_delay: int,
        reconnect_max: int,
        timeout_connect: int,
        callback_connected: Callable[[], None],
        callback_disconnected: Callable[[Exception], None],
        callback_data: Callable[[bytes], int],
    ) -> None:
        """Initialize a transport instance.

        :param comm_name: name of this transport connection
        :param reconnect_delay: delay in milliseconds for first reconnect (0 for no reconnect)
        :param reconnect_delay: max reconnect delay in milliseconds
        :param timeout_connect: Max. time in milliseconds for connect to complete
        :param callback_connected: Called when connection is established
        :param callback_disconnected: Called when connection is disconnected
        :param callback_data: Called when data is received
        """
        self.cb_connection_made = callback_connected
        self.cb_connection_lost = callback_disconnected
        self.cb_handle_data = callback_data

        # properties, can be read, but may not be mingled with
        self.comm_params = self.CommParamsClass(
            comm_name=comm_name,
            reconnect_delay=reconnect_delay / 1000,
            reconnect_delay_max=reconnect_max / 1000,
            timeout_connect=timeout_connect / 1000,
        )

        self.reconnect_delay_current: float = 0.0
        self.transport: asyncio.BaseTransport | asyncio.Server = None
        self.protocol: asyncio.BaseProtocol = None
        self.loop: asyncio.AbstractEventLoop = None
        with suppress(RuntimeError):
            self.loop = asyncio.get_running_loop()
        self.reconnect_task: asyncio.Task = None
        self.recv_buffer: bytes = b""
        self.call_connect_listen: Callable[[], Coroutine[Any, Any, Any]] = lambda: None
        self.use_udp = False

    # ------------------------ #
    # Transport specific setup #
    # ------------------------ #
    def setup_unix(self, setup_server: bool, host: str):
        """Prepare transport unix"""
        if sys.platform.startswith("win"):
            raise RuntimeError("Modbus_unix is not supported on Windows!")
        self.comm_params.check_done()
        self.comm_params.done = True
        self.comm_params.host = host
        if setup_server:
            self.call_connect_listen = lambda: self.loop.create_unix_server(
                self.handle_listen,
                path=self.comm_params.host,
                start_serving=True,
            )
        else:
            self.call_connect_listen = lambda: self.loop.create_unix_connection(
                lambda: self,
                path=self.comm_params.host,
            )

    def setup_tcp(self, setup_server: bool, host: str, port: int):
        """Prepare transport tcp"""
        self.comm_params.check_done()
        self.comm_params.done = True
        self.comm_params.host = host
        self.comm_params.port = port
        if setup_server:
            self.call_connect_listen = lambda: self.loop.create_server(
                self.handle_listen,
                host=self.comm_params.host,
                port=self.comm_params.port,
                reuse_address=True,
                start_serving=True,
            )
        else:
            self.call_connect_listen = lambda: self.loop.create_connection(
                lambda: self,
                host=self.comm_params.host,
                port=self.comm_params.port,
            )

    def setup_tls(
        self,
        setup_server: bool,
        host: str,
        port: int,
        sslctx: ssl.SSLContext,
        certfile: str,
        keyfile: str,
        password: str,
        server_hostname: str,
    ):
        """Prepare transport tls"""
        self.comm_params.check_done()
        self.comm_params.done = True
        self.comm_params.host = host
        self.comm_params.port = port
        self.comm_params.server_hostname = server_hostname
        if not sslctx:
            # According to MODBUS/TCP Security Protocol Specification, it is
            # TLSv2 at least
            sslctx = ssl.SSLContext(
                ssl.PROTOCOL_TLS_SERVER if setup_server else ssl.PROTOCOL_TLS_CLIENT
            )
            sslctx.check_hostname = False
            sslctx.verify_mode = ssl.CERT_NONE
            sslctx.options |= ssl.OP_NO_TLSv1_1
            sslctx.options |= ssl.OP_NO_TLSv1
            sslctx.options |= ssl.OP_NO_SSLv3
            sslctx.options |= ssl.OP_NO_SSLv2
            if certfile:
                sslctx.load_cert_chain(
                    certfile=certfile, keyfile=keyfile, password=password
                )
        self.comm_params.ssl = sslctx
        if setup_server:
            self.call_connect_listen = lambda: self.loop.create_server(
                self.handle_listen,
                host=self.comm_params.host,
                port=self.comm_params.port,
                reuse_address=True,
                ssl=self.comm_params.ssl,
                start_serving=True,
            )
        else:
            self.call_connect_listen = lambda: self.loop.create_connection(
                lambda: self,
                self.comm_params.host,
                self.comm_params.port,
                ssl=self.comm_params.ssl,
                server_hostname=self.comm_params.server_hostname,
            )

    def setup_udp(self, setup_server: bool, host: str, port: int):
        """Prepare transport udp"""
        self.comm_params.check_done()
        self.comm_params.done = True
        self.comm_params.host = host
        self.comm_params.port = port
        if setup_server:

            async def call_async_listen(self):
                """Remove protocol return value."""
                transport, _protocol = await self.loop.create_datagram_endpoint(
                    self.handle_listen,
                    local_addr=(self.comm_params.host, self.comm_params.port),
                )
                return transport

            self.call_connect_listen = lambda: call_async_listen(self)
        else:
            self.call_connect_listen = lambda: self.loop.create_datagram_endpoint(
                lambda: self,
                remote_addr=(self.comm_params.host, self.comm_params.port),
            )
        self.use_udp = True

    def setup_serial(
        self,
        setup_server: bool,
        host: str,
        baudrate: int,
        bytesize: int,
        parity: str,
        stopbits: int,
    ):
        """Prepare transport serial"""
        self.comm_params.check_done()
        self.comm_params.done = True
        self.comm_params.host = host
        self.comm_params.baudrate = baudrate
        self.comm_params.bytesize = bytesize
        self.comm_params.parity = parity
        self.comm_params.stopbits = stopbits
        if setup_server:
            self.call_connect_listen = lambda: create_serial_connection(
                self.loop,
                self.handle_listen,
                self.comm_params.host,
                baudrate=self.comm_params.baudrate,
                bytesize=self.comm_params.bytesize,
                parity=self.comm_params.parity,
                stopbits=self.comm_params.stopbits,
                timeout=self.comm_params.timeout_connect,
            )

        else:
            self.call_connect_listen = lambda: create_serial_connection(
                self.loop,
                lambda: self,
                self.comm_params.host,
                baudrate=self.comm_params.baudrate,
                bytesize=self.comm_params.bytesize,
                stopbits=self.comm_params.stopbits,
                parity=self.comm_params.parity,
                timeout=self.comm_params.timeout_connect,
            )

    async def transport_connect(self):
        """Handle generic connect and call on to specific transport connect."""
        Log.debug("Connecting {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        self.transport, self.protocol = None, None
        try:
            self.transport, self.protocol = await asyncio.wait_for(
                self.call_connect_listen(),
                timeout=self.comm_params.timeout_connect,
            )
        except (
            asyncio.TimeoutError,
            OSError,
        ) as exc:
            Log.warning("Failed to connect {}", exc)
            self.close(reconnect=True)
        return self.transport, self.protocol

    async def transport_listen(self):
        """Handle generic listen and call on to specific transport listen."""
        Log.debug("Awaiting connections {}", self.comm_params.comm_name)
        try:
            self.transport = await self.call_connect_listen()
        except OSError as exc:
            Log.warning("Failed to start server {}", exc)
            self.close()
        return self.transport

    # ---------------------------------- #
    # Transport asyncio standard methods #
    # ---------------------------------- #
    def connection_made(self, transport: asyncio.BaseTransport):
        """Call from asyncio, when a connection is made.

        :param transport: socket etc. representing the connection.
        """
        Log.debug("Connected to {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        self.transport = transport
        self.reset_delay()
        self.cb_connection_made()

    def connection_lost(self, reason: Exception):
        """Call from asyncio, when the connection is lost or closed.

        :param reason: None or an exception object
        """
        Log.debug("Connection lost {} due to {}", self.comm_params.comm_name, reason)
        self.cb_connection_lost(reason)
        if self.transport:
            self.close()
            self.reconnect_task = asyncio.create_task(self.reconnect_connect())

    def eof_received(self):
        """Call when eof received (other end closed connection).

        Handling is moved to connection_lost()
        """

    def data_received(self, data: bytes):
        """Call when some data is received.

        :param data: non-empty bytes object with incoming data.
        """
        Log.debug("recv: {}", data, ":hex")
        self.recv_buffer += data
        cut = self.cb_handle_data(self.recv_buffer)
        self.recv_buffer = self.recv_buffer[cut:]

    def datagram_received(self, data, _addr):
        """Receive datagram (UDP connections)."""
        self.data_received(data)

    # -------------------------------- #
    # Helper methods for child classes #
    # -------------------------------- #
    async def send(self, data: bytes) -> bool:
        """Send request.

        :param data: non-empty bytes object with data to send.
        """
        Log.debug("send: {}", data, ":hex")
        if self.use_udp:
            return self.transport.sendto(data)  # type: ignore[union-attr]
        return self.transport.write(data)  # type: ignore[union-attr]

    def close(self, reconnect: bool = False) -> None:
        """Close connection.

        :param reconnect: (default false), try to reconnect
        """
        if self.transport:
            if hasattr(self.transport, "abort"):
                self.transport.abort()
            self.transport.close()
            self.transport = None
        self.protocol = None
        if not reconnect and self.reconnect_task:
            self.reconnect_task.cancel()
            self.reconnect_task = None
        self.recv_buffer = b""

    def reset_delay(self) -> None:
        """Reset wait time before next reconnect to minimal period."""
        self.reconnect_delay_current = self.comm_params.reconnect_delay

    # ---------------- #
    # Internal methods #
    # ---------------- #
    def handle_listen(self):
        """Handle incoming connect."""
        return self

    async def reconnect_connect(self):
        """Handle reconnect as a task."""
        try:
            self.reconnect_delay_current = self.comm_params.reconnect_delay
            transport = None
            while not transport:
                Log.debug(
                    "Wait {} {} ms before reconnecting.",
                    self.comm_params.comm_name,
                    self.reconnect_delay_current * 1000,
                )
                await asyncio.sleep(self.reconnect_delay_current)
                transport, _protocol = await self.transport_connect()
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
        self.close()

    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_params.comm_name})"
