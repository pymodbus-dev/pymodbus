"""Modbus client async TCP communication."""
from __future__ import annotations

import asyncio
import select
import socket
import time
from typing import Any

from pymodbus.client.base import ModbusBaseClient, ModbusBaseSyncClient
from pymodbus.exceptions import ConnectionException
from pymodbus.framer import Framer
from pymodbus.logging import Log
from pymodbus.transport import CommType


class AsyncModbusTcpClient(ModbusBaseClient, asyncio.Protocol):
    """**AsyncModbusTcpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication
    :param source_address: source address of client

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

        from pymodbus.client import AsyncModbusTcpClient

        async def run():
            client = AsyncModbusTcpClient("localhost")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    socket: socket.socket | None

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: Framer = Framer.SOCKET,
        source_address: tuple[str, int] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Asyncio Modbus TCP Client."""
        asyncio.Protocol.__init__(self)
        if "CommType" not in kwargs:
            kwargs["CommType"] = CommType.TCP
        if source_address:
            kwargs["source_address"] = source_address
        ModbusBaseClient.__init__(
            self,
            framer,
            host=host,
            port=port,
            **kwargs,
        )

    async def connect(self) -> bool:
        """Initiate connection to start client."""
        self.reset_delay()
        Log.debug(
            "Connecting to {}:{}.",
            self.comm_params.host,
            self.comm_params.port,
        )
        return await self.base_connect()

    def close(self, reconnect: bool = False) -> None:  # type: ignore[override]
        """Close connection."""
        super().close(reconnect=reconnect)


class ModbusTcpClient(ModbusBaseSyncClient):
    """**ModbusTcpClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication
    :param source_address: source address of client

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

        from pymodbus.client import ModbusTcpClient

        async def run():
            client = ModbusTcpClient("localhost")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.

    Remark: There are no automatic reconnect as with AsyncModbusTcpClient
    """

    socket: socket.socket | None

    def __init__(
        self,
        host: str,
        port: int = 502,
        framer: Framer = Framer.SOCKET,
        source_address: tuple[str, int] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize Modbus TCP Client."""
        if "CommType" not in kwargs:
            kwargs["CommType"] = CommType.TCP
        super().__init__(
            framer,
            host=host,
            port=port,
            **kwargs,
        )
        self.params.source_address = source_address
        self.socket = None

    @property
    def connected(self) -> bool:
        """Connect internal."""
        return self.socket is not None

    def connect(self):
        """Connect to the modbus tcp server."""
        if self.socket:
            return True
        try:
            self.socket = socket.create_connection(
                (self.comm_params.host, self.comm_params.port),
                timeout=self.comm_params.timeout_connect,
                source_address=self.params.source_address,
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
        super().send(request)
        if not self.socket:
            raise ConnectionException(str(self))
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

        return b"".join(data)

    def _handle_abrupt_socket_close(self, size, data, duration):
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

    def is_socket_open(self):
        """Check if socket is open."""
        return self.socket is not None

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, timeout={self.comm_params.timeout_connect}>"
        )
