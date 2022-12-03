"""Base for all transport types."""
from __future__ import annotations

from abc import abstractmethod
from typing import Any

from pymodbus.framer import ModbusFramer
from pymodbus.logging import Log


class BaseTransport:
    """Base class for transport types.

    :param framer: framer used to encode/decode data
    :param slaves: list of acceptable slaves (0 for accept all)
    :param comm_name: name of this transport connection
    :param reconnect_delay: delay in milliseconds for first reconnect (0 for no reconnect)
    :param reconnect_delay_max: max delay in milliseconds for next reconnect, resets to reconnect_delay
    :param retries_send: number of times to retry a send operation
    :param retry_on_empty: retry read on nothing
    :param timeout_connect: Max. time in milliseconds for connect to complete
    :param timeout_comm: Max. time in milliseconds for recv/send to complete

    :property reconnect_delay_current: current delay in milliseconds for next reconnect (doubles with every try)
    :property transport: current transport class (none if not connected)

    BaseTransport contains functions common to all transport types and client/server.

    This class is not available in the pymodbus API, and should not be referenced in Applications.
    """

    def __init__(
        self,
        framer: ModbusFramer,
        slaves: list[int],
        comm_name: str = "NO NAME",
        reconnect_delay: int = 0,
        reconnect_delay_max: int = 0,
        retries_send: int = 0,
        retry_on_empty: bool = False,
        timeout_connect: int = 10,
        timeout_comm: int = 5,
    ) -> None:
        """Initialize a transport instance."""
        # parameter variables
        self.framer = framer
        self.slaves = slaves
        self.comm_name = comm_name
        self.reconnect_delay = reconnect_delay
        self.reconnect_delay_max = reconnect_delay_max
        self.retries_send = retries_send
        self.retry_on_empty = retry_on_empty
        self.timeout_connect = timeout_connect
        self.timeout_comm = timeout_comm

        # local variables
        self.reconnect_delay_current: int = 0
        self.transport: Any = None

    # -------------------------- #
    # Transport external methods #
    # -------------------------- #
    def connection_made(self, transport):
        """Call when a connection is made.

        The transport argument is the transport representing the connection.
        """
        self.transport = transport
        Log.debug("Connected on transport {}", transport)
        self.cb_connection_made()

    def connection_lost(self, reason):
        """Call when the connection is lost or closed.

        The argument is either an exception object or None
        """
        self.transport = None
        if reason:
            Log.debug(
                "Connection lost due to {} on transport {}", reason, self.transport
            )
        self.cb_connection_lost(reason)

    def data_received(self, data):
        """Call when some data is received.

        data is a non-empty bytes object containing the incoming data.
        """
        Log.debug("recv: {}", data, ":hex")
        # self.framer.processIncomingPacket(data, self._handle_response, unit=0)

    def send(self, request: bytes) -> bool:
        """Send request."""
        return self.cb_send(request)

    def close(self) -> None:
        """Close the underlying socket connection (call **sync/async**)."""
        # raise NotImplementedException

    # -------------------------- #
    # Transport callback methods #
    # -------------------------- #
    @abstractmethod
    def cb_connection_made(self) -> bool:
        """Handle low level."""

    @abstractmethod
    def cb_connection_lost(self, _reason) -> bool:
        """Handle low level."""

    @abstractmethod
    def cb_send(self, _request) -> bool:
        """Handle low level."""

    @abstractmethod
    def cb_close(self) -> bool:
        """Handle low level."""

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self) -> BaseTransport:
        """Implement the client with enter block."""
        return self

    async def __aenter__(self):
        """Implement the client with enter block."""
        return self

    def __exit__(self, _class, _value, _traceback) -> None:
        """Implement the client with exit block."""
        self.close()

    async def __aexit__(self, _class, _value, _traceback) -> None:
        """Implement the client with exit block."""
        self.close()

    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_name})"
