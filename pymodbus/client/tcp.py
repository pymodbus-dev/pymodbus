"""Modbus client async TCP communication."""
import asyncio
import logging
import select
import socket
import time
import typing

from pymodbus.client.base import ModbusBaseClient, ModbusClientProtocol
from pymodbus.constants import Defaults
from pymodbus.framer import ModbusFramer
from pymodbus.framer.socket_framer import ModbusSocketFramer
from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import ModbusTransactionState

_logger = logging.getLogger(__name__)


class AsyncModbusTcpClient(ModbusBaseClient):
    """**AsyncModbusTcpClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) source address of client,
    :param kwargs: (optional) Experimental parameters

    Example::

        from pymodbus.client import AsyncModbusTcpClient

        async def run():
            client = AsyncModbusTcpClient("localhost")

            await client.connect()
            ...
            await client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = Defaults.TcpPort,
        framer: ModbusFramer = ModbusSocketFramer,
        source_address: typing.Tuple[str, int] = None,
        **kwargs: any,
    ) -> None:
        """Initialize Asyncio Modbus TCP Client."""
        self.protocol = None
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address
        self.loop = None
        self.connected = False
        self.delay_ms = self.params.reconnect_delay

    async def connect(self):  # pylint: disable=invalid-overridden-method
        """Initiate connection to start client."""
        # force reconnect if required:
        self.loop = asyncio.get_running_loop()

        txt = f"Connecting to {self.params.host}:{self.params.port}."
        _logger.debug(txt)
        return await self._connect()

    async def close(self):  # pylint: disable=invalid-overridden-method
        """Stop client."""
        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

        # prevent reconnect.
        self.params.host = None

    def _create_protocol(self):
        """Create initialized protocol instance with factory function."""
        protocol = ModbusClientProtocol(framer=self.params.framer, **self.params.kwargs)
        protocol.factory = self
        return protocol

    async def _connect(self):
        """Connect."""
        _logger.debug("Connecting.")
        try:
            transport, protocol = await self.loop.create_connection(
                self._create_protocol, host=self.params.host, port=self.params.port
            )
            return transport, protocol
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())
        else:
            txt = f"Connected to {self.params.host}:{self.params.port}."
            _logger.info(txt)
            self.reset_delay()

    def protocol_made_connection(self, protocol):
        """Notify successful connection."""
        _logger.info("Protocol made connection.")
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    def protocol_lost_connection(self, protocol):
        """Notify lost connection."""
        _logger.info("Protocol lost connection.")
        if protocol is not self.protocol:
            _logger.error(
                "Factory protocol callback called from unexpected protocol instance."
            )

        self.connected = False
        self.protocol = None
        if self.params.host:
            asyncio.ensure_future(self._reconnect())

    async def _reconnect(self):
        """Reconnect."""
        txt = f"Waiting {self.delay_ms} ms before next connection attempt."
        _logger.debug(txt)
        await asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = 2 * self.delay_ms

        return await self._connect()


class ModbusTcpClient(ModbusBaseClient):
    """**ModbusTcpClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication.
    :param framer: (optional) Framer class.
    :param source_address: (optional) source address of client,
    :param kwargs: (optional) Experimental parameters

    Example::

        from pymodbus.client import ModbusTcpClient

        async def run():
            client = ModbusTcpClient("localhost")

            client.connect()
            ...
            client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = Defaults.TcpPort,
        framer: ModbusFramer = ModbusSocketFramer,
        source_address: typing.Tuple[str, int] = None,
        **kwargs: any,
    ) -> None:
        """Initialize Modbus TCP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address
        self.socket = None

    @property
    def connected(self):
        """Connect internal."""
        return self.connect()

    def connect(self):
        """Connect to the modbus tcp server."""
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.params.host, self.params.port),
                timeout=self.params.timeout,
                source_address=self.params.source_address,
            )
            txt = f"Connection to Modbus server established. Socket {self.socket.getsockname()}"
            _logger.debug(txt)
        except socket.error as msg:
            txt = (
                f"Connection to ({self.params.host}, {self.params.port}) failed: {msg}"
            )
            _logger.error(txt)
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def _check_read_buffer(self):
        """Check read buffer."""
        time_ = time.time()
        end = time_ + self.params.timeout
        data = None
        ready = select.select([self.socket], [], [], end - time_)
        if ready[0]:
            data = self.socket.recv(1024)
        return data

    def send(self, request):
        """Send data on the underlying socket."""
        super().send(request)
        if not self.socket:
            raise ConnectionException(str(self))
        if self.state == ModbusTransactionState.RETRYING:
            if data := self._check_read_buffer():
                return data

        if request:
            return self.socket.send(request)
        return 0

    def recv(self, size):
        """Read data from the underlying descriptor."""
        super().recv(size)
        if not self.socket:
            raise ConnectionException(str(self))

        # socket.recv(size) waits until it gets some data from the host but
        # not necessarily the entire response that can be fragmented in
        # many packets.
        # To avoid split responses to be recognized as invalid
        # messages and to be discarded, loops socket.recv until full data
        # is received or timeout is expired.
        # If timeout expires returns the read data, also if its length is
        # less than the expected size.
        self.socket.setblocking(0)

        timeout = self.params.timeout

        # If size isn"t specified read up to 4096 bytes at a time.
        if size is None:
            recv_size = 4096
        else:
            recv_size = size

        data = []
        data_length = 0
        time_ = time.time()
        end = time_ + timeout
        while recv_size > 0:
            try:
                ready = select.select([self.socket], [], [], end - time_)
            except ValueError:
                return self._handle_abrupt_socket_close(size, data, time.time() - time_)
            if ready[0]:
                if (recv_data := self.socket.recv(recv_size)) == b"":
                    return self._handle_abrupt_socket_close(
                        size, data, time.time() - time_
                    )
                data.append(recv_data)
                data_length += len(recv_data)
            time_ = time.time()

            # If size isn"t specified continue to read until timeout expires.
            if size:
                recv_size = size - data_length

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn"t an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break

        return b"".join(data)

    def _handle_abrupt_socket_close(
        self, size, data, duration
    ):  # pylint: disable=missing-type-doc
        """Handle unexpected socket close by remote end.

        Intended to be invoked after determining that the remote end
        has unexpectedly closed the connection, to clean up and handle
        the situation appropriately.

        :param size: The number of bytes that was attempted to read
        :param data: The actual data returned
        :param duration: Duration from the read was first attempted
               until it was determined that the remote closed the
               socket
        :return: The more than zero bytes read from the remote end
        :raises ConnectionException: If the remote end didn't send any
                 data at all before closing the connection.
        """
        self.close()
        size_txt = size if size else "unbounded read"
        readsize = f"read of {size_txt} bytes"
        msg = (
            f"{self}: Connection unexpectedly closed "
            f"{duration} seconds into {readsize}"
        )
        if data:
            result = b"".join(data)
            msg += f" after returning {len(result)} bytes"
            _logger.warning(msg)
            return result
        msg += " without response from unit before it closed connection"
        raise ConnectionException(msg)

    def is_socket_open(self):
        """Check if socket is open."""
        return self.socket is not None

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"ModbusTcpClient({self.params.host}:{self.params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.params.host}, port={self.params.port}, timeout={self.params.timeout}>"
        )
