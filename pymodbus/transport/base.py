"""Base for all transport types."""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log


class BaseTransport:
    """Base class for transport types.

    BaseTransport contains functions common to all transport types and client/server.

    This class is not available in the pymodbus API, and should not be referenced in Applications.
    """

    def __init__(self) -> None:
        """Initialize a transport instance."""
        # parameter variables, overwritten in child classes
        self.framer: ModbusFramer | None = None
        # -> framer: framer used to encode/decode data
        self.slaves: list[int] = []
        # -> slaves: list of acceptable slaves (0 for accept all)
        self.comm_name: str = ""
        # -> comm_name: name of this transport connection
        self.reconnect_delay: int = -1
        # -> reconnect_delay: delay in milliseconds for first reconnect (0 for no reconnect)
        self.reconnect_delay_max: int = -1
        # -> reconnect_delay_max: max delay in milliseconds for next reconnect, resets to reconnect_delay
        self.retries_send: int = -1
        # -> retries_send: number of times to retry a send operation
        self.retry_on_empty: int = -1
        # -> retry_on_empty: retry read on nothing
        self.timeout_connect: bool = None
        # -> timeout_connect: Max. time in milliseconds for connect to complete
        self.timeout_comm: int = -1
        # -> timeout_comm: Max. time in milliseconds for recv/send to complete
        self.on_connection_made: Callable[[str], None] = lambda x: None
        # -> on_connection_made: callback when connection is established and opened
        self.on_connection_lost: Callable[[str, Exception], None] = lambda x, y: None
        # -> on_connection_lost: callback when connection is lost and closed

        # properties, can be read, but may not be mingled with
        self.reconnect_delay_current: int = 0
        # -> reconnect_delay_current: current delay in milliseconds for next reconnect (doubles with every try)
        self.transport: Any = None
        # -> transport: current transport class (None if not connected)
        self.loop = asyncio.get_event_loop()
        # -> loop: current asyncio event loop

    # -------------------------------------------- #
    # Transport external methods (asyncio defined) #
    # -------------------------------------------- #
    def connection_made(self, transport: Any):
        """Call from asyncio, when a connection is made.

        :param transport: socket etc. representing the connection.
        """
        self.transport = transport
        Log.debug("Connected {}", self.comm_name)
        self.on_connection_made(self.comm_name)

    def connection_lost(self, reason: Exception):
        """Call from asyncio, when the connection is lost or closed.

        :param reason: None or an exception object
        """
        self.transport = None
        Log.debug("Connection lost {} due to {}", self.comm_name, reason)
        self.on_connection_lost(self.comm_name, reason)

    def data_received(self, data: bytes):
        """Call when some data is received.

        :param data: non-empty bytes object with incoming data.
        """
        Log.debug("recv: {}", data, ":hex")
        # self.framer.processIncomingPacket(data, self._handle_response, unit=0)

    def datagram_received(self, data, _addr):
        """Receive datagram."""
        self.data_received(data)

    def send(self, data: bytes) -> bool:
        """Send request.

        :param data: non-empty bytes object with data to send.
        """
        Log.debug("send: {}", data, ":hex")
        return False

    def close(self) -> None:
        """Close the underlying  connection."""

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    async def __aenter__(self):
        """Implement the client with async enter block."""
        return self

    async def __aexit__(self, _class, _value, _traceback) -> None:
        """Implement the client with async exit block."""
        self.close()

    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_name})"
