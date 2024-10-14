"""Modbus client async UDP communication."""
from __future__ import annotations

import socket
import time
from collections.abc import Callable

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType


DGRAM_TYPE = socket.SOCK_DGRAM


class AsyncModbusUdpClient(ModbusBaseClient):
    """**AsyncModbusUdpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param framer: Framer name, default FramerType.SOCKET
    :param port: Port used for communication.
    :param name: Set communication name, used in logging
    :param source_address: source address of client,
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param timeout: Timeout for connecting and receiving data, in seconds.
    :param retries: Max number of retries per request.
    :param on_connect_callback: Function that will be called just before a connection attempt.

    .. tip::
        **reconnect_delay** doubles automatically with each unsuccessful connect, from
        **reconnect_delay** to **reconnect_delay_max**.
        Set `reconnect_delay=0` to avoid automatic reconnection.

    Example::

        from pymodbus.client import AsyncModbusUdpClient

        async def run():
            client = AsyncModbusUdpClient("localhost")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        framer: FramerType = FramerType.SOCKET,
        port: int = 502,
        name: str = "comm",
        source_address: tuple[str, int] | None = None,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
        on_connect_callback: Callable[[bool], None] | None = None,
    ) -> None:
        """Initialize Asyncio Modbus UDP Client."""
        self.comm_params = CommParams(
            comm_type=CommType.UDP,
            host=host,
            port=port,
            comm_name=name,
            source_address=source_address,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        ModbusBaseClient.__init__(
            self,
            framer,
            retries,
            on_connect_callback,
        )
        self.source_address = source_address


class ModbusUdpClient(ModbusBaseSyncClient):
    """**ModbusUdpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param framer: Framer name, default FramerType.SOCKET
    :param port: Port used for communication.
    :param name: Set communication name, used in logging
    :param source_address: source address of client,
    :param reconnect_delay: Not used in the sync client
    :param reconnect_delay_max: Not used in the sync client
    :param timeout: Timeout for connecting and receiving data, in seconds.
    :param retries: Max number of retries per request.

    .. tip::
        Unlike the async client, the sync client does not perform
        retries. If the connection has closed, the client will attempt to reconnect
        once before executing each read/write request, and will raise a
        ConnectionException if this fails.

    Example::

        from pymodbus.client import ModbusUdpClient

        async def run():
            client = ModbusUdpClient("localhost")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    socket: socket.socket | None

    def __init__(
        self,
        host: str,
        framer: FramerType = FramerType.SOCKET,
        port: int = 502,
        name: str = "comm",
        source_address: tuple[str, int] | None = None,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
    ) -> None:
        """Initialize Modbus UDP Client."""
        self.comm_params = CommParams(
            comm_type=CommType.UDP,
            host=host,
            port=port,
            comm_name=name,
            source_address=source_address,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        super().__init__(framer, retries)
        self.socket = None

    @property
    def connected(self) -> bool:
        """Connect internal."""
        return self.socket is not None

    def connect(self):
        """Connect to the modbus tcp server.

        :meta private:
        """
        if self.socket:
            return True
        try:
            family = ModbusUdpClient.get_address_family(self.comm_params.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.comm_params.timeout_connect)
        except OSError as exc:
            Log.error("Unable to create udp socket {}", exc)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection.

        :meta private:
        """
        self.socket = None

    def send(self, request: bytes) -> int:
        """Send data on the underlying socket.

        :meta private:
        """
        super()._start_send()
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            return self.socket.sendto(
                request, (self.comm_params.host, self.comm_params.port)
            )
        return 0

    def recv(self, size: int | None) -> bytes:
        """Read data from the underlying descriptor.

        :meta private:
        """
        if not self.socket:
            raise ConnectionException(str(self))
        if size is None:
            size = 0
        data = self.socket.recvfrom(size)[0]
        self.last_frame_end = round(time.time(), 6)
        return data

    def is_socket_open(self):
        """Check if socket is open.

        :meta private:
        """
        return True

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, timeout={self.comm_params.timeout_connect}>"
        )
