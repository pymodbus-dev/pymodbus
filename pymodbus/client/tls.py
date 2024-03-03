"""Modbus client async TLS communication."""
from __future__ import annotations

import socket
import ssl
from typing import Any

from pymodbus.client.tcp import AsyncModbusTcpClient, ModbusTcpClient
from pymodbus.framer import Framer
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType


class AsyncModbusTlsClient(AsyncModbusTcpClient):
    """**AsyncModbusTlsClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication
    :param source_address: Source address of client
    :param sslctx: SSLContext to use for TLS
    :param certfile: Cert file path for TLS server request
    :param keyfile: Key file path for TLS server request
    :param password: Password for for decrypting private key file
    :param server_hostname: Bind certificate to host

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

        from pymodbus.client import AsyncModbusTlsClient

        async def run():
            client = AsyncModbusTlsClient("localhost")

            await client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.
    """

    def __init__(
        self,
        host: str,
        port: int = 802,
        framer: Framer = Framer.TLS,
        sslctx: ssl.SSLContext | None = None,
        certfile: str | None = None,
        keyfile: str | None = None,
        password: str | None = None,
        server_hostname: str | None = None,
        **kwargs: Any,
    ):
        """Initialize Asyncio Modbus TLS Client."""
        AsyncModbusTcpClient.__init__(
            self,
            host,
            port=port,
            framer=framer,
            CommType=CommType.TLS,
            sslctx=CommParams.generate_ssl(
                False, certfile, keyfile, password, sslctx=sslctx
            ),
            **kwargs,
        )
        self.server_hostname = server_hostname

    async def connect(self) -> bool:
        """Initiate connection to start client."""
        self.reset_delay()
        Log.debug(
            "Connecting to {}:{}.",
            self.comm_params.host,
            self.comm_params.port,
        )
        return await self.base_connect()


class ModbusTlsClient(ModbusTcpClient):
    """**ModbusTlsClient**.

    Fixed parameters:

    :param host: Host IP address or host name

    Optional parameters:

    :param port: Port used for communication
    :param source_address: Source address of client
    :param sslctx: SSLContext to use for TLS
    :param certfile: Cert file path for TLS server request
    :param keyfile: Key file path for TLS server request
    :param password: Password for decrypting private key file
    :param server_hostname: Bind certificate to host
    :param kwargs: Experimental parameters

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

        from pymodbus.client import ModbusTlsClient

        async def run():
            client = ModbusTlsClient("localhost")

            client.connect()
            ...
            client.close()

    Please refer to :ref:`Pymodbus internals` for advanced usage.

    Remark: There are no automatic reconnect as with AsyncModbusTlsClient
    """

    def __init__(
        self,
        host: str,
        port: int = 802,
        framer: Framer = Framer.TLS,
        sslctx: ssl.SSLContext | None = None,
        certfile: str | None = None,
        keyfile: str | None = None,
        password: str | None = None,
        server_hostname: str | None = None,
        **kwargs: Any,
    ):
        """Initialize Modbus TLS Client."""
        super().__init__(
            host, CommType=CommType.TLS, port=port, framer=framer, **kwargs
        )
        self.sslctx = CommParams.generate_ssl(
            False, certfile, keyfile, password, sslctx=sslctx
        )
        self.server_hostname = server_hostname

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
            if self.params.source_address:
                sock.bind(self.params.source_address)
            self.socket = self.sslctx.wrap_socket(
                sock, server_side=False, server_hostname=self.server_hostname
            )
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
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, sslctx={self.sslctx}, "
            f"timeout={self.comm_params.timeout_connect}>"
        )
