"""Null modem transport.

This is a special transport, mostly thought of for testing.

NullModem interconnect 2 transport objects and transfers calls:
    - client/server.connect()
        - call client.connection_made()
        - call server.connection_made()
    - client/server.close()
        - call client.connection_lost()
        - call server.connection_lost()
    - server.close()
        - call server.connection_lost()
        - call client.connection_lost()
    - server/client.send
        - call client/server.data_received()

"""
from __future__ import annotations

import asyncio

from pymodbus.logging import Log
from pymodbus.transport.transport import Transport


class NullModem(Transport):
    """Transport layer.

    Contains pure transport methods needed to connect/listen, send/receive and close connections
    for unix socket, tcp, tls and serial communications.

    Contains high level methods like reconnect.

    This class is not available in the pymodbus API, and should not be referenced in Applications
    nor in the pymodbus documentation.

    The class is designed to be an object in the message level class.
    """


    async def transport_connect(self) -> bool:
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
            return False
        return bool(self.transport)

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

    def is_active(self) -> bool:
        """Return true if connected/listening."""
        return bool(self.transport)

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
        self.close()

    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_params.comm_name})"
