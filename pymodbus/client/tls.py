"""Modbus client async TLS communication."""
from __future__ import annotations

import socket
import ssl
from collections.abc import Callable

from pymodbus.client.tcp import AsyncModbusTcpClient, ModbusTcpClient
from pymodbus.framer import FramerType
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType


class AsyncModbusTlsClient(AsyncModbusTcpClient):
    """**AsyncModbusTlsClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param sslctx: SSLContext to use for TLS
    :param framer: Framer name, default FramerType.TLS
    :param port: Port used for communication
    :param name: Set communication name, used in logging
    :param source_address: Source address of client
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

        from pymodbus.client import AsyncModbusTlsClient

        async def run():
            client = AsyncModbusTlsClient("localhost")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        sslctx: ssl.SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        framer: FramerType = FramerType.TLS,
        port: int = 802,
        name: str = "comm",
        source_address: tuple[str, int] | None = None,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
        on_connect_callback: Callable[[bool], None] | None = None,
    ):
        """Initialize Asyncio Modbus TLS Client."""
        self.comm_params = CommParams(
            comm_type=CommType.TLS,
            host=host,
            sslctx=sslctx,
            port=port,
            comm_name=name,
            source_address=source_address,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        AsyncModbusTcpClient.__init__(
            self,
            "",
            framer=framer,
            retries=retries,
            on_connect_callback=on_connect_callback,
        )

    @classmethod
    def generate_ssl(
        cls,
        certfile: str | None = None,
        keyfile: str | None = None,
        password: str | None = None,
    ) -> ssl.SSLContext:
        """Generate sslctx from cert/key/password.

        :param certfile: Cert file path for TLS server request
        :param keyfile: Key file path for TLS server request
        :param password: Password for for decrypting private key file

        Remark:
        - MODBUS/TCP Security Protocol Specification demands TLSv2 at least
        - verify_mode is set to ssl.NONE
        """
        return CommParams.generate_ssl(
            False, certfile=certfile, keyfile=keyfile, password=password
        )

class ModbusTlsClient(ModbusTcpClient):
    """**ModbusTlsClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param sslctx: SSLContext to use for TLS
    :param framer: Framer name, default FramerType.TLS
    :param port: Port used for communication
    :param name: Set communication name, used in logging
    :param source_address: Source address of client
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

        from pymodbus.client import ModbusTlsClient

        async def run():
            client = ModbusTlsClient("localhost")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        sslctx: ssl.SSLContext = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        framer: FramerType = FramerType.TLS,
        port: int = 802,
        name: str = "comm",
        source_address: tuple[str, int] | None = None,
        reconnect_delay: float = 0.1,
        reconnect_delay_max: float = 300,
        timeout: float = 3,
        retries: int = 3,
    ):
        """Initialize Modbus TLS Client."""
        self.comm_params = CommParams(
            comm_type=CommType.TLS,
            host=host,
            sslctx=sslctx,
            port=port,
            comm_name=name,
            source_address=source_address,
            reconnect_delay=reconnect_delay,
            reconnect_delay_max=reconnect_delay_max,
            timeout_connect=timeout,
        )
        super().__init__(
            "",
            framer=framer,
            retries=retries,
        )

    @classmethod
    def generate_ssl(
        cls,
        certfile: str | None = None,
        keyfile: str | None = None,
        password: str | None = None,
    ) -> ssl.SSLContext:
        """Generate sslctx from cert/key/password.

        :param certfile: Cert file path for TLS server request
        :param keyfile: Key file path for TLS server request
        :param password: Password for for decrypting private key file

        Remark:
        - MODBUS/TCP Security Protocol Specification demands TLSv2 at least
        - verify_mode is set to ssl.NONE
        """
        return CommParams.generate_ssl(
            False, certfile=certfile, keyfile=keyfile, password=password,
        )

    @property
    def connected(self) -> bool:
        """Connect internal."""
        return self.transport is not None

    def connect(self):
        """Connect to the modbus tls server."""
        if self.socket:
            return True
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.comm_params.source_address:
                sock.bind(self.comm_params.source_address)
            self.socket = self.comm_params.sslctx.wrap_socket(sock, server_side=False)  # type: ignore[union-attr]
            self.socket.settimeout(self.comm_params.timeout_connect)
            self.socket.connect((self.comm_params.host, self.comm_params.port))
        except OSError as msg:
            Log.error(
                "Connection to ({}, {}) failed: {}",
                self.comm_params.host,
                self.comm_params.port,
                msg,
            )
            self.close()
        return self.socket is not None

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, sslctx={self.comm_params.sslctx}, "
            f"timeout={self.comm_params.timeout_connect}>"
        )
