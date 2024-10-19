"""Modbus client async TCP communication."""
from __future__ import annotations

import select
import socket
import time
from collections.abc import Callable

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType


class AsyncModbusTcpClient(ModbusBaseClient):
    """**AsyncModbusTcpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param framer: Framer name, default FramerType.SOCKET
    :param port: Port used for communication
    :param name: Set communication name, used in logging
    :param source_address: source address of client
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

        from pymodbus.client import AsyncModbusTcpClient

        async def run():
            client = AsyncModbusTcpClient("localhost")

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
        """Initialize Asyncio Modbus TCP Client."""
        if not hasattr(self,"comm_params"):
            self.comm_params = CommParams(
                comm_type=CommType.TCP,
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


class ModbusTcpClient(ModbusBaseSyncClient):
    """**ModbusTcpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param framer: Framer name, default FramerType.SOCKET
    :param port: Port used for communication
    :param name: Set communication name, used in logging
    :param source_address: source address of client
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

        from pymodbus.client import ModbusTcpClient

        async def run():
            client = ModbusTcpClient("localhost")

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
        """Initialize Modbus TCP Client."""
        if not hasattr(self,"comm_params"):
            self.comm_params = CommParams(
                comm_type=CommType.TCP,
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
        """Check if socket exists."""
        return self.socket is not None

    def connect(self):
        """Connect to the modbus tcp server."""
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.comm_params.host, self.comm_params.port),
                timeout=self.comm_params.timeout_connect,
                source_address=self.comm_params.source_address,
            )
            Log.debug(
                "Connection to Modbus server established. Socket {}",
                self.socket.getsockname(),
            )
        except OSError as msg:
            Log.error(
                "Connection to ({}, {}) failed: {}",
                self.comm_params.host,
                self.comm_params.port,
                msg,
            )
            self.close()
        return self.socket is not None

    def close(self):
        """Close the underlying socket connection."""
        if self.socket:
            self.socket.close()
        self.socket = None

    def send(self, request):
        """Send data on the underlying socket."""
        super()._start_send()
        if not self.socket:
            raise ConnectionException(str(self))
        if request:
            return self.socket.send(request)
        return 0

    def recv(self, size: int | None) -> bytes:
        """Read data from the underlying descriptor."""
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
        self.socket.setblocking(False)

        timeout = self.comm_params.timeout_connect or 0

        # If size isn't specified read up to 4096 bytes at a time.
        if size is None:
            recv_size = 4096
        else:
            recv_size = size

        data: list[bytes] = []
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

            # If size isn't specified continue to read until timeout expires.
            if size:
                recv_size = size - data_length

            # Timeout is reduced also if some data has been received in order
            # to avoid infinite loops when there isn't an expected response
            # size and the slave sends noisy data continuously.
            if time_ > end:
                break
        self.last_frame_end = round(time.time(), 6)
        return b"".join(data)

    def _handle_abrupt_socket_close(self, size: int | None, data: list[bytes], duration: float) -> bytes:
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
            f"{duration:.3f} seconds into {readsize}"
        )
        if data:
            result = b"".join(data)
            Log.warning(" after returning {} bytes: {} ", len(result), result)
            return result
        msg += " without response from slave before it closed connection"
        raise ConnectionException(msg)

    def is_socket_open(self) -> bool:
        """Check if socket is open."""
        return self.socket is not None

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, timeout={self.comm_params.timeout_connect}>"
        )
