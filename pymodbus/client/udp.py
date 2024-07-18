"""Modbus client async UDP communication."""
from __future__ import annotations

import socket
from typing import Any

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.transport import CommType


DGRAM_TYPE = socket.SOCK_DGRAM


class AsyncModbusUdpClient(ModbusBaseClient):
    """**AsyncModbusUdpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication.
    :param source_address: source address of client,

    Common optional parameters:

    :param framer: Framer enum name
    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    Example::

        from pymodbus.client import AsyncModbusUdpClient

        async def run():
            client = AsyncModbusUdpClient("localhost")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: FramerType = FramerType.SOCKET,
        source_address: tuple[str, int] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus UDP Client."""
        ModbusBaseClient.__init__(
            self,
            framer,
            CommType=CommType.UDP,
            host=host,
            port=port,
            **kwargs,
        )
        self.source_address = source_address

    @property
    def connected(self):
        """Return true if connected."""
        return self.ctx.is_active()


class ModbusUdpClient(ModbusBaseSyncClient):
    """**ModbusUdpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication.
    :param source_address: source address of client,

    Common optional parameters:

    :param framer: Framer enum name
    :param timeout: Timeout for a request, in seconds.
    :param retries: Max number of retries per request.
    :param retry_on_empty: Retry on empty response.
    :param broadcast_enable: True to treat id 0 as broadcast address.
    :param reconnect_delay: Minimum delay in seconds.milliseconds before reconnecting.
    :param reconnect_delay_max: Maximum delay in seconds.milliseconds before reconnecting.
    :param on_reconnect_callback: Function that will be called just before a reconnection attempt.
    :param no_resend_on_retry: Do not resend request when retrying due to missing response.
    :param kwargs: Experimental parameters.

    Example::

        from pymodbus.client import ModbusUdpClient

        async def run():
            client = ModbusUdpClient("localhost")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.

    Remark: There are no automatic reconnect as with AsyncModbusUdpClient
    """

    socket: socket.socket | None

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: FramerType = FramerType.SOCKET,
        source_address: tuple[str, int] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus UDP Client."""
        super().__init__(
            framer,
            port=port,
            host=host,
            CommType=CommType.UDP,
            **kwargs,
        )
        self.params.source_address = source_address

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
        return self.socket.recvfrom(size)[0]

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
