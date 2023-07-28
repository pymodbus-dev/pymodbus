"""Modbus client async TLS communication."""
import socket
import ssl
from typing import Any, Type

from pymodbus.client.tcp import AsyncModbusTcpClient, ModbusTcpClient
from pymodbus.framer import ModbusFramer
from pymodbus.framer.tls_framer import ModbusTlsFramer
from pymodbus.logging import Log
from pymodbus.transport import CommParams, CommType


class AsyncModbusTlsClient(AsyncModbusTcpClient):
    """**AsyncModbusTlsClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication
    :param framer: (optional) Framer class
    :param source_address: (optional) Source address of client
    :param sslctx: (optional) SSLContext to use for TLS
    :param certfile: (optional) Cert file path for TLS server request
    :param keyfile: (optional) Key file path for TLS server request
    :param password: (optional) Password for for decrypting private key file
    :param server_hostname: (optional) Bind certificate to host
    :param kwargs: (optional) Experimental parameters

    ..tip::
        See ModbusBaseClient for common parameters.

    Example::

        from pymodbus.client import AsyncModbusTlsClient

        async def run():
            client = AsyncModbusTlsClient("localhost")

            await client.connect()
            ...
            client.close()
    """

    def __init__(
        self,
        host: str,
        port: int = 802,
        framer: Type[ModbusFramer] = ModbusTlsFramer,
        sslctx: ssl.SSLContext = None,
        certfile: str = None,
        keyfile: str = None,
        password: str = None,
        server_hostname: str = None,
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
        self.params.server_hostname = server_hostname

    async def connect(self) -> bool:
        """Initiate connection to start client."""

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


class ModbusTlsClient(ModbusTcpClient):
    """**ModbusTlsClient**.

    :param host: Host IP address or host name
    :param port: (optional) Port used for communication
    :param framer: (optional) Framer class
    :param source_address: (optional) Source address of client
    :param sslctx: (optional) SSLContext to use for TLS
    :param certfile: (optional) Cert file path for TLS server request
    :param keyfile: (optional) Key file path for TLS server request
    :param password: (optional) Password for decrypting private key file
    :param server_hostname: (optional) Bind certificate to host
    :param kwargs: (optional) Experimental parameters

    ..tip::
        See ModbusBaseClient for common parameters.

    Example::

        from pymodbus.client import ModbusTlsClient

        async def run():
            client = ModbusTlsClient("localhost")

            client.connect()
            ...
            client.close()


    Remark: There are no automatic reconnect as with AsyncModbusTlsClient
    """

    def __init__(
        self,
        host: str,
        port: int = 802,
        framer: Type[ModbusFramer] = ModbusTlsFramer,
        sslctx: ssl.SSLContext = None,
        certfile: str = None,
        keyfile: str = None,
        password: str = None,
        server_hostname: str = None,
        **kwargs: Any,
    ):
        """Initialize Modbus TLS Client."""
        self.transport = None
        super().__init__(
            host, CommType=CommType.TLS, port=port, framer=framer, **kwargs
        )
        self.sslctx = CommParams.generate_ssl(
            False, certfile, keyfile, password, sslctx=sslctx
        )
        self.params.server_hostname = server_hostname

    @property
    def connected(self):
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
                sock, server_side=False, server_hostname=self.comm_params.host
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

    def __str__(self):
        """Build a string representation of the connection."""
        return f"ModbusTlsClient({self.comm_params.host}:{self.comm_params.port})"

    def __repr__(self):
        """Return string representation."""
        return (
            f"<{self.__class__.__name__} at {hex(id(self))} socket={self.socket}, "
            f"ipaddr={self.comm_params.host}, port={self.comm_params.port}, sslctx={self.sslctx}, "
            f"timeout={self.comm_params.timeout_connect}>"
        )
