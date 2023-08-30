"""Modbus client async UDP communication."""
import asyncio
import socket
from typing import Any, Tuple, Type

from pymodbus.client.base import ModbusBaseClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import ModbusFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.logging import Log
from pymodbus.transport import CommType


DGRAM_TYPE = socket.SOCK_DGRAM


class AsyncModbusUdpClient(
    ModbusBaseClient, asyncio.Protocol, asyncio.DatagramProtocol
):
    """**AsyncModbusUdpClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) source address of client,
    :param kwargs: (optional) Experimental parameters

    ..tip::
        See ModbusBaseClient for common parameters.

    Example::

        from pymodbus.client import AsyncModbusUdpClient

        async def run():
            client = AsyncModbusUdpClient("localhost")

            await client.connect()
            ...
            client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: Type[ModbusFramer] = ModbusSocketFramer,
        source_address: Tuple[str, int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus UDP Client."""
        asyncio.DatagramProtocol.__init__(self)
        asyncio.Protocol.__init__(self)
        ModbusBaseClient.__init__(
            self, framer=framer, CommType=CommType.UDP, host=host, port=port, **kwargs
        )
        self.params.source_address = source_address

    @property
    def connected(self):
        """Return true if connected."""
        return self.is_active()

    async def connect(self) -> bool:
        """Start reconnecting asynchronous udp client.

        :meta private:
        """
        # if reconnect_delay_current was set to 0 by close(), we need to set it back again
        # so this instance will work
        self.reset_delay()

        # force reconnect if required:
        Log.debug(
            "Connecting to {}:{}.",
            self.comm_params.host,
            self.comm_params.port,
        )
        return await self.transport_connect()


class ModbusUdpClient(ModbusBaseClient):
    """**ModbusUdpClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) source address of client,
    :param kwargs: (optional) Experimental parameters

    ..tip::
        See ModbusBaseClient for common parameters.

    Example::

        from pymodbus.client import ModbusUdpClient

        async def run():
            client = ModbusUdpClient("localhost")

            client.connect()
            ...
            client.close()

    Remark: There are no automatic reconnect as with AsyncModbusUdpClient
    """

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: Type[ModbusFramer] = ModbusSocketFramer,
        source_address: Tuple[str, int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus UDP Client."""
        kwargs["use_sync"] = True
        self.transport = None
        super().__init__(
            framer=framer, port=port, host=host, CommType=CommType.UDP, **kwargs
        )
        self.params.source_address = source_address

        self.socket = None

    @property
    def connected(self):
        """Connect internal."""
        return self.socket is not None

    def connect(self):  # pylint: disable=invalid-overridden-method
        """Connect to the modbus tcp server.

        :meta private:
        """
        if self.socket:
            return True
        try:
            family = ModbusUdpClient._get_address_family(self.comm_params.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.comm_params.timeout_connect)
        except OSError as exc:
            Log.error("Unable to create udp socket {}", exc)
            self.close()
        return self.socket is not None

    def close(self):  # pylint: disable=arguments-differ
        """Close the underlying socket connection.

        :meta private:
        """
        self.socket = None

    def send(self, request):
        """Send data on the underlying socket.

        :meta private:
        """
        super().send(request)
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            return self.socket.sendto(
                request, (self.comm_params.host, self.comm_params.port)
            )
        return 0

    def recv(self, size):
        """Read data from the underlying descriptor.

        :meta private:
        """
        super().recv(size)
        if not self.socket:
            raise ConnectionException(str(self))
        return self.socket.recvfrom(size)[0]

    def is_socket_open(self):
        """Check if socket is open.

        :meta private:
        """
        return True

    def __str__(self):
        """Build a string representation of the connection."""
        return f"ModbusUdpClient({self.comm_params.host}:{self.comm_params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, timeout={self.comm_params.timeout_connect}>"
        )
