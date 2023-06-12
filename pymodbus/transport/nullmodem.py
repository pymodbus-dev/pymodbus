"""Null modem transport.

This is a special transport, mostly thought of for testing.

NullModem interconnect 2 transport objects and transfers calls:
    - server.listen()
        - dummy
    - client.connect()
        - call client.connection_made()
        - call server.connection_made()
    - client/server.close()
        - call client.connection_lost()
        - call server.connection_lost()
    - server/client.send
        - call client/server.data_received()

"""
from __future__ import annotations

import asyncio

from pymodbus.logging import Log
from pymodbus.transport.transport import Transport


class DummyTransport(asyncio.BaseTransport):
    """Use in connection_made calls."""

    def close(self):
        """Define dummy."""

    def get_protocol(self):
        """Define dummy."""

    def is_closing(self):
        """Define dummy."""

    def set_protocol(self, _protocol):
        """Define dummy."""

    def abort(self):
        """Define dummy."""


class NullModem(Transport):
    """Transport layer.

    Contains pure transport methods needed to connect/listen, send/receive and close connections
    for unix socket, tcp, tls and serial communications.

    Contains high level methods like reconnect.

    This class is not available in the pymodbus API, and should not be referenced in Applications
    nor in the pymodbus documentation.

    The class is designed to be an object in the message level class.
    """

    server: NullModem = None
    client: NullModem = None
    is_server: bool = False

    async def transport_connect(self) -> bool:
        """Handle generic connect and call on to specific transport connect."""
        self.is_server = False
        self.client = self
        Log.debug("NullModem: Simulate connect on {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        self.transport, self.protocol = None, None
        if self.server:
            self.server.connection_made(self.DummyTransport())
            self.connection_made(self.DummyTransport())
            return True
        return False

    async def transport_listen(self):
        """Handle generic listen and call on to specific transport listen."""
        self.is_server = True
        self.server = self
        Log.debug("NullModem: Simulate listen on {}", self.comm_params.comm_name)
        return self.DummyTransport()

    # -------------------------------- #
    # Helper methods for child classes #
    # -------------------------------- #
    async def send(self, data: bytes) -> bool:
        """Send request.

        :param data: non-empty bytes object with data to send.
        """
        Log.debug("NullModem: simulate send {}", data, ":hex")
        if self.is_server:
            self.client.data_received(data)
        else:
            self.server.data_received(data)
        return True

    def close(self, reconnect: bool = False) -> None:
        """Close connection.

        :param reconnect: (default false), try to reconnect
        """
        self.recv_buffer = b""
        if not reconnect:
            self.client.cb_connection_lost(None)
            self.server.cb_connection_lost(None)

    def is_active(self) -> bool:
        """Return true if connected/listening."""
        return True

    # ----------------- #
    # The magic methods #
    # ----------------- #
    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_params.comm_name})"
