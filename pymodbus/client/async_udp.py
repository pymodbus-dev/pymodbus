"""**Modbus client async UDP communication.**

Example::

    from pymodbus.client import AsyncModbusUdpClient

    async def run():
        client = AsyncModbusUdpClient(
            "127.0.0.1",
            # Common optional paramers:
            #    port=502,
            #    modbus_decoder=ClientDecoder,
            #    framer=ModbusSocketFramer,
            #    timeout=10,
            #    retries=3,
            #    retry_on_empty=False,
            #    close_comm_on_error=False,
            #    strict=True,
            # UDP setup parameters
            #    source_address=("localhost", 0),
        )

        await client.aConnect()
        ...
        await client.aClose()
"""
import asyncio
import logging
import functools
import socket

from pymodbus.client.base import ModbusBaseClient
from pymodbus.transaction import ModbusSocketFramer
# from pymodbus.client.helper_async import ModbusClientProtocol
from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import hexlify_packets

_logger = logging.getLogger(__name__)

DGRAM_TYPE = socket.SOCK_DGRAM


class ModbusUdpClientProtocol(ModbusBaseClient, asyncio.DatagramProtocol):
    """Asyncio specific implementation of asynchronous modbus udp client protocol."""

    #: Factory that created this instance.
    factory = None
    transport = None

    def __init__(
        self,
        host="127.0.0.1",
        port=502,
        framer=None,
        source_address=None,
        timeout=10,
        **kwargs,
    ):
        """Initialize a Modbus TCP/UDP asynchronous client

        :param host: Host IP address
        :param port: Port
        :param framer: Framer to use
        :param source_address: Specific to underlying client being used
        :param timeout: Timeout in seconds
        :param kwargs: Extra arguments
        """
        self.host = host
        self.port = port
        self.source_address = source_address or ("", 0)
        self._timeout = timeout
        self._connected = False
        super().__init__(framer=framer or ModbusSocketFramer, **kwargs)

    def datagram_received(self, data, addr):
        """Receive datagram."""
        self._data_received(data)

    def write_transport(self, packet):
        """Write transport."""
        return self.transport.sendto(packet)

    async def execute(self, request=None):  # pylint: disable=invalid-overridden-method
        """Execute requests asynchronously."""
        req = self._execute(request)
        if self.params.broadcast_enable and not request.unit_id:
            resp = b"Broadcast write sent - no response expected"
        else:
            resp = await asyncio.wait_for(req, timeout=self._timeout)
        return resp

    def connection_made(self, transport):
        """Call when a connection is made.

        The transport argument is the transport representing the connection.
        """
        self.transport = transport
        self._connection_made()

        if self.factory:
            self.factory.protocol_made_connection(self)  # pylint: disable=no-member

    def connection_lost(self, reason):
        """Call when the connection is lost or closed."""
        self.transport = None
        self._connection_lost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(self)  # pylint: disable=no-member

    def data_received(self, data):
        """Call when some data is received."""
        self._data_received(data)

    def create_future(self):
        """Create asyncio Future object."""
        return asyncio.Future()

    def resolve_future(self, my_future, result):
        """Resolve future."""
        if not my_future.done():
            my_future.set_result(result)

    def raise_future(self, my_future, exc):
        """Set exception of a future if not done."""
        if not my_future.done():
            my_future.set_exception(exc)

    def _connection_made(self):
        """Call upon a successful client connection."""
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def _connection_lost(self, reason):
        """Call upon a client disconnect."""
        txt = f"Client disconnected from modbus server: {reason}"
        _logger.debug(txt)
        self._connected = False
        for tid in list(self.transaction):
            self.raise_future(
                self.transaction.getTransaction(tid),
                ConnectionException("Connection lost during request"),
            )

    @property
    def connected(self):
        """Return connection status."""
        return self._connected

    def _execute(self, request, **kwargs):  # NOSONAR pylint: disable=unused-argument
        """Start the producer to send the next request to consumer.write(Frame(request))."""
        request.transaction_id = self.transaction.getNextTID()
        packet = self.framer.buildPacket(request)
        txt = f"send: {hexlify_packets(packet)}"
        _logger.debug(txt)
        self.write_transport(packet)
        return self._build_response(request.transaction_id)

    def _data_received(self, data):
        """Get response, check for valid message, decode result."""
        txt = f"recv: {hexlify_packets(data)}"
        _logger.debug(txt)
        unit = self.framer.decode_data(data).get("unit", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)

    def _handle_response(self, reply, **kwargs):  # pylint: disable=unused-argument
        """Handle the processed response and link to correct deferred."""
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                self.resolve_future(handler, reply)
            else:
                txt = f"Unrequested message: {str(reply)}"
                _logger.debug(txt)

    def _build_response(self, tid):
        """Return a deferred response for the current request."""
        my_future = self.create_future()
        if not self._connected:
            self.raise_future(my_future, ConnectionException("Client is not connected"))
        else:
            self.transaction.addTransaction(my_future, tid)
        return my_future

    async def aClose(self):
        """Close."""
        self.transport.close()
        self._connected = False


class AsyncModbusUdpClient(ModbusBaseClient):
    r"""Modbus client for async UDP communication.

    :param host: (positional) Host IP address
    :param port: (optional default 502) The serial port used for communication.
    :param framer: (optional, default ModbusSocketFramer) Framer class.
    :param source_address: (optional, default none) source address of client,
    :param \*\*kwargs: (optional) Extra experimental parameters for transport
    :return: client object
    """

    #: Reconnect delay in milli seconds.
    delay_ms = 0
    #: Maximum delay in milli seconds before reconnect is attempted.
    DELAY_MAX_MS = 1000 * 60 * 5

    def __init__(
        self,
        host,
        port=502,
        framer=ModbusSocketFramer,
        source_address="127.0.0.1",
        **kwargs,
    ):
        """Initialize Asyncio Modbus UDP Client."""
        super().__init__(framer=framer, **kwargs)
        self.params.host = host
        self.params.port = port
        self.source_address = source_address

        self.loop = asyncio.get_event_loop()
        self.protocol = None
        self.connected = False
        self.reset_delay()

    def reset_delay(self):
        """Reset wait before next reconnect to minimal period."""
        self.delay_ms = 100

    async def aConnect(self):
        """Start reconnecting asynchronous udp client."""
        # force reconnect if required:
        host = self.params.host
        await self.aClose()
        self.params.host = host

        # get current loop, if there are no loop a RuntimeError will be raised
        self.loop = asyncio.get_running_loop()

        txt = f"Connecting to {self.params.host}:{self.params.port}."
        _logger.debug(txt)

        # getaddrinfo returns a list of tuples
        # - [(family, type, proto, canonname, sockaddr),]
        # We want sockaddr which is a (ip, port) tuple
        # udp needs ip addresses, not hostnames
        # TBD: addrinfo = await self.loop.getaddrinfo(self.params.host, self.params.port, type=DGRAM_TYPE)
        # TBD: self.params.host, self.params.port = addrinfo[-1][-1]
        return await self._connect()

    async def aClose(self):
        """Stop connection and prevents reconnect."""
        # prevent reconnect:
        self.params.host = None

        if self.connected and self.protocol and self.protocol.transport:
            self.protocol.transport.close()

    def _create_protocol(self, host=None, port=0):
        """Create initialized protocol instance with factory function."""
        protocol = ModbusUdpClientProtocol(
            use_udp=True,
            framer=self.params.framer,
            **self.params.kwargs
        )
        protocol.params.host = host
        protocol.params.port = port
        protocol.factory = self
        return protocol

    async def _connect(self):
        """Connect."""
        _logger.debug("Connecting.")
        try:
            endpoint = await self.loop.create_datagram_endpoint(
                functools.partial(
                    self._create_protocol, host=self.params.host, port=self.params.port
                ),
                remote_addr=(self.params.host, self.params.port),
            )
            txt = f"Connected to {self.params.host}:{self.params.port}."
            _logger.info(txt)
            return endpoint
        except Exception as exc:  # pylint: disable=broad-except
            txt = f"Failed to connect: {exc}"
            _logger.warning(txt)
            asyncio.ensure_future(self._reconnect())

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
        if self.connected:
            _logger.info("Protocol lost connection.")
            if protocol is not self.protocol:
                _logger.error(
                    "Factory protocol callback called "
                    "from unexpected protocol instance."
                )

            self.connected = False
            self.protocol = None
            if self.params.host:
                asyncio.create_task(self._reconnect())
        else:
            _logger.error("Factory protocol connect callback called while connected.")

    async def _reconnect(self):
        """Reconnect."""
        txt = f"Waiting {self.delay_ms} ms before next connection attempt."
        _logger.debug(txt)
        await asyncio.sleep(self.delay_ms / 1000)
        self.delay_ms = min(2 * self.delay_ms, self.DELAY_MAX_MS)
        return await self._connect()
