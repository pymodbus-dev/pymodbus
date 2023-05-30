"""Modbus client async UDP communication."""
import asyncio
import socket
from typing import Any, Tuple, Type

from pymodbus.client.base import ModbusBaseClient
from pymodbus.constants import Defaults
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import ModbusFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.logging import Log


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
        port: int = Defaults.UdpPort,
        framer: Type[ModbusFramer] = ModbusSocketFramer,
        source_address: Tuple[str, int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus UDP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address

    @property
    def connected(self):
        """Return true if connected."""
        return self.transport is not None

    async def connect(self):
        """Start reconnecting asynchronous udp client.

        :meta private:
        """
        # get current loop, if there are no loop a RuntimeError will be raised
        Log.debug("Connecting to {}:{}.", self.params.host, self.params.port)

        # getaddrinfo returns a list of tuples
        # - [(family, type, proto, canonname, sockaddr),]
        # We want sockaddr which is a (ip, port) tuple
        # udp needs ip addresses, not hostnames
        # TBD: addrinfo = await getaddrinfo(self.params.host, self.params.port, type=DGRAM_TYPE)
        # TBD: self.params.host, self.params.port = addrinfo[-1][-1]
        return await self._connect()

    def _create_protocol(self):
        """Create initialized protocol instance with function."""
        self.use_udp = True
        return self

    async def _connect(self):
        """Connect."""
        Log.debug("Connecting.")
        try:
            endpoint = await self.loop.create_datagram_endpoint(
                self._create_protocol,
                remote_addr=(self.params.host, self.params.port),
            )
            Log.info("Connected to {}:{}.", self.params.host, self.params.port)
            return endpoint
        except Exception as exc:  # pylint: disable=broad-except
            Log.warning("Failed to connect: {}", exc)
            self.close(reconnect=True)
        self.reset_delay()


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
        port: int = Defaults.UdpPort,
        framer: Type[ModbusFramer] = ModbusSocketFramer,
        source_address: Tuple[str, int] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus UDP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address

        self.socket = None
        self.use_sync = True

    def connect(self):  # pylint: disable=invalid-overridden-method
        """Connect to the modbus tcp server.

        :meta private:
        """
        if self.socket:
            return True
        try:
            family = ModbusUdpClient._get_address_family(self.params.host)
            self.socket = socket.socket(family, socket.SOCK_DGRAM)
            self.socket.settimeout(self.params.timeout)
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
            return self.socket.sendto(request, (self.params.host, self.params.port))
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
        return f"ModbusUdpClient({self.params.host}:{self.params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.params.host}, port={self.params.port}, timeout={self.params.timeout}>"
        )
