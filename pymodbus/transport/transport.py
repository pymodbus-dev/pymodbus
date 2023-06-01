"""Base for all transport types."""
from __future__ import annotations

import asyncio
from abc import abstractmethod
from contextlib import suppress

from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log


class BaseTransport:
    """Base class for transport types.

    BaseTransport contains functions common to all transport types and client/server.

    This class is not available in the pymodbus API, and should not be referenced in Applications.
    """

    def __init__(
        self,
        comm_name: str,
        framer: ModbusFramer,
        reconnect_delay: int,
        reconnect_delay_max: int,
        timeout_connect: int,
        timeout_comm: int,
    ) -> None:
        """Initialize a transport instance.

        :param comm_name: name of this transport connection
        :param framer: framer used to encode/decode data
        :param reconnect_delay: delay in milliseconds for first reconnect (0 for no reconnect)
        :param reconnect_delay_max: max delay in milliseconds for next reconnect
        :param timeout_connect: Max. time in milliseconds for connect to complete
        :param timeout_comm: Max. time in milliseconds for send to complete
        """
        self.comm_name = comm_name
        self.framer = framer
        self.reconnect_delay = reconnect_delay
        self.reconnect_delay_max = reconnect_delay_max
        self.timeout_connect = timeout_connect
        self.timeout_comm = timeout_comm

        # properties, can be read, but may not be mingled with
        self.reconnect_delay_current = self.reconnect_delay
        self.transport: asyncio.BaseTransport = None
        with suppress(RuntimeError):
            self.loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self.reconnect_timer: asyncio.TimerHandle = None
        self.recv_buffer: bytes = b""

    # ---------------------------------- #
    # Transport asyncio standard methods #
    # ---------------------------------- #
    def connection_made(self, transport: asyncio.BaseTransport):
        """Call from asyncio, when a connection is made.

        :param transport: socket etc. representing the connection.
        """
        Log.debug("Connected {}", self.comm_name)
        self.transport = transport
        self.cb_connection_made()

    def connection_lost(self, reason: Exception):
        """Call from asyncio, when the connection is lost or closed.

        :param reason: None or an exception object
        """
        Log.debug("Connection lost {} due to {}", self.comm_name, reason)
        self.cb_connection_lost(reason)
        self.close(reconnect=True)

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

    # --------------------------------- #
    # callback methods in child classes #
    # --------------------------------- #
    @abstractmethod
    def cb_handle_data(self, _data: bytes) -> int:
        """Handle received data

        returns number of bytes consumed
        """

    @abstractmethod
    def cb_connection_made(self) -> None:
        """Handle new connection"""

    @abstractmethod
    def cb_connection_lost(self, _reason: Exception) -> None:
        """Handle lost connection"""

    @abstractmethod
    async def connect(self):
        """Connect to the modbus remote host."""

    # -------------------------------- #
    # Helper methods for child classes #
    # -------------------------------- #
    async def send(self, data: bytes) -> bool:
        """Send request.

        :param data: non-empty bytes object with data to send.
        """
        Log.debug("send: {}", data, ":hex")
        return False

    def close(self, reconnect: bool = False) -> None:
        """Close connection.

        :param reconnect: (default false), try to reconnect
        """
        if self.transport:
            self.transport.abort()  # type: ignore[attr-defined]
            self.transport.close()
            self.transport = None
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
        self.recv_buffer = b""

        if not reconnect or not self.reconnect_delay_current:
            self.reconnect_delay_current = 0
            return

        Log.debug("Waiting {} ms reconnecting.", self.reconnect_delay_current)
        self.reconnect_timer = self.loop.call_later(
            self.reconnect_delay_current / 1000, asyncio.create_task, self.connect()
        )
        self.reconnect_delay_current = min(
            2 * self.reconnect_delay_current, self.reconnect_delay_max
        )

    def complete_connect(self, connected=True):
        """Handle transport layer connect."""
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
        if not connected:
            self.close(reconnect=True)
            return
        self.reset_delay()

    def reset_delay(self) -> None:
        """Reset wait time before next reconnect to minimal period."""
        self.reconnect_delay_current = self.reconnect_delay

    # ---------------- #
    # Internal methods #
    # ---------------- #

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
        return f"{self.__class__.__name__}({self.comm_name})"
