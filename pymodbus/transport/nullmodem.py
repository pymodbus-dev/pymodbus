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

    Contains methods to act as a null modem between 2 objects.
    (Allowing tests to be shortcut without actual network calls)
    """

    nullmodem_client: NullModem = None
    nullmodem_server: NullModem = None

    def __init__(self, *arg):
        """Overwrite init."""
        self.is_server: bool = False
        self.other_end: NullModem = None
        super().__init__(*arg)

    async def transport_connect(self) -> bool:
        """Handle generic connect and call on to specific transport connect."""
        Log.debug("NullModem: Simulate connect on {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        if self.nullmodem_server:
            self.__class__.nullmodem_client = self
            self.other_end = self.nullmodem_server
            self.cb_connection_made()
            self.other_end.cb_connection_made()
            return True
        return False

    async def transport_listen(self):
        """Handle generic listen and call on to specific transport listen."""
        Log.debug("NullModem: Simulate listen on {}", self.comm_params.comm_name)
        if not self.loop:
            self.loop = asyncio.get_running_loop()
        self.is_server = True
        self.__class__.nullmodem_server = self
        return DummyTransport()

    # -------------------------------- #
    # Helper methods for child classes #
    # -------------------------------- #
    async def send(self, data: bytes) -> bool:
        """Send request.

        :param data: non-empty bytes object with data to send.
        """
        Log.debug("NullModem: simulate send {}", data, ":hex")
        self.other_end.data_received(data)
        return True

    def close(self, reconnect: bool = False) -> None:
        """Close connection.

        :param reconnect: (default false), try to reconnect
        """
        self.recv_buffer = b""
        if not reconnect:
            self.nullmodem_client.cb_connection_lost(None)
            self.nullmodem_server.cb_connection_lost(None)
            self.__class__.nullmodem_client = None
            self.__class__.nullmodem_server = None

    # ----------------- #
    # The magic methods #
    # ----------------- #
    def __str__(self) -> str:
        """Build a string representation of the connection."""
        return f"{self.__class__.__name__}({self.comm_params.comm_name})"
