"""**Modbus Client common base.**

All client share a set of parameters as well as all methods available to applications,
are defined in :mod:`ModbusBaseClient`.

:mod:`ModbusBaseClient` is normally not referenced outside :mod:`pymodbus`, unless
you want to make a custom client. Custom client class **must** inherit
:mod:`ModbusBaseClient`.

Custom client implementation example::

    from pymodbus.client import ModbusBaseClient

    class myOwnClient(ModbusBaseClient):

        def __init__(self, **kwargs):
            super().__init__(kwargs)

    def run():

        client = myOwnClient(...)
        client.connect()
        rr = client.read_coils(0x01)
        client.close()

.. tip::
    Parameters common for all clients are documented here, and not repeated with each
    client, this is in order to lower the maintenance burden and the risk of the
    documentation being inaccurate.
"""
from __future__ import annotations
from dataclasses import dataclass
import asyncio
import logging

from pymodbus.utilities import hexlify_packets
from pymodbus.factory import ClientDecoder
from pymodbus.utilities import ModbusTransactionState
from pymodbus.transaction import DictTransactionManager
from pymodbus.client.mixin import ModbusClientMixin
from pymodbus.exceptions import (
    NotImplementedException,
    ConnectionException,
)
from pymodbus.framer import ModbusFramer


_logger = logging.getLogger(__name__)

TXT_NOT_IMPLEMENTED = "Method not implemented by derived class"


class ModbusBaseClient(ModbusClientMixin):
    """Base functionality common to all clients.

    :param modbus_decoder: (optional, default ClientDecoder) Modbus message decoder class.
    :param framer: (optional, default depend on client) Modbus Framer class.
    :param timeout: (optional, default 10s) Timeout for a request.
    :param retries: (optional, default 3) Max number of retries pr request.
    :param retry_on_empty: (optional, default false) Retry on empty response.
    :param close_comm_on_error: (optional, default true) Close connection on error.
    :param strict: (optional, default true) Strict timing, 1.5 character between requests.
    :param broadcast_enable: (optional, default false) True to treat id 0 as broadcast address.

    Handles common parameters and defines an internal interface
    which all clients must adhere to.

    Implements common functionality like e.g. `reconnect`.
    """

    @dataclass
    class _params:  # pylint: disable=too-many-instance-attributes
        """Common parameters."""

        host: str = None
        port: str | int = None
        modbus_decoder: ClientDecoder = None
        framer: ModbusFramer = None
        timeout: int = None
        retries: int = None
        retry_on_empty: bool = None
        close_comm_on_error: bool = None
        strict: bool = None
        broadcast_enable: bool = None
        kwargs: dict = None

    def __init__(
        self,
        modbus_decoder=ClientDecoder,
        framer=None,
        timeout=10,
        retries=3,
        retry_on_empty=False,
        close_comm_on_error=True,
        strict=True,
        broadcast_enable=False,
        **kwargs
    ):
        """Initialize a client instance."""
        self.params = self._params()
        self.params.framer = framer
        self.params.timeout = int(timeout)
        self.params.retries = int(retries)
        self.params.retry_on_empty = bool(retry_on_empty)
        self.params.close_comm_on_error = bool(close_comm_on_error)
        self.params.strict = bool(strict)
        self.params.broadcast_enable = bool(broadcast_enable)
        self.params.kwargs = kwargs

        # Common variables.
        self.framer = self.params.framer(modbus_decoder(), self)
        self.transaction = DictTransactionManager(self, **kwargs)

        # Initialize  mixin
        super().__init__()

    # ----------------------------------------------------------------------- #
    # Client external interface
    # ----------------------------------------------------------------------- #
    def register(self, function):  # pylint: disable=missing-type-doc
        """Register a function and sub function class with the decoder.

        :param function: Custom function class to register
        """
        self.framer.decoder.register(function)

    def connect(self):
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    async def aConnect(self):
        """Connect to the modbus remote host.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    def is_socket_open(self):
        """Check whether the underlying socket/serial is open or not.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    def idle_time(self):
        """Bus Idle Time to initiate next transaction

        :return: time stamp
        """
        if self.last_frame_end is None or self.silent_interval is None:
            return 0
        return self.last_frame_end + self.silent_interval

    def execute(self, request=None):  # pylint: disable=missing-type-doc
        """Execute.

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException:
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{str(self)}]")
        return self.transaction.execute(request)

    async def aExecute(self, request=None):  # pylint: disable=missing-type-doc
        """Execute.

        :param request: The request to process
        :returns: The result of the request execution
        :raises ConnectionException:
        """
        return self.execute(request=request)

    def send(self, request):
        """Send request."""
        if self.state != ModbusTransactionState.RETRYING:
            _logger.debug('New Transaction state "SENDING"')
            self.state = ModbusTransactionState.SENDING
        return request

    async def aSend(self, request):
        """Send request."""
        return self.send(request)

    def recv(self, size):
        """Receive data."""
        return size

    async def aRecv(self, size):
        """Receive data."""
        return self.recv(size)

    def close(self):
        """Close the underlying socket connection.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    async def aClose(self):
        """Close the underlying socket connection.

        :raises NotImplementedException:
        """
        raise NotImplementedException(TXT_NOT_IMPLEMENTED)

    # ----------------------------------------------------------------------- #
    # The magic methods
    # ----------------------------------------------------------------------- #
    def __enter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not self.connect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    async def __aenter__(self):
        """Implement the client with enter block.

        :returns: The current instance of the client
        :raises ConnectionException:
        """
        if not await self.aConnect():
            raise ConnectionException(f"Failed to connect[{self.__str__()}]")
        return self

    def __exit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        self.close()

    async def __aexit__(self, klass, value, traceback):
        """Implement the client with exit block."""
        await self.aClose()

    def __str__(self):
        """Build a string representation of the connection.

        :returns: The string representation
        """
        return f"{self.__class__.__name__} {self.params.host}:{self.params.port}"


class ModbusClientProtocol(
    ModbusBaseClient,
    asyncio.Protocol,
    asyncio.DatagramProtocol,
):
    """Asyncio specific implementation of asynchronous modbus client protocol."""

    #: Factory that created this instance.
    factory = None
    transport = None

    def __init__(
        self,
        host="127.0.0.1",
        port=502,
        source_address=None,
        use_udp=False,
        **kwargs
    ):
        """Initialize a Modbus TCP/UDP asynchronous client"""
        super().__init__(**kwargs)
        self.use_udp = use_udp
        self.params.host = host
        self.params.port = port
        self.params.source_address = source_address or ("", 0)

        self._connected = False

    def datagram_received(self, data, addr):
        """Receive datagram."""
        self._data_received(data)

    async def execute(self, request=None):  # pylint: disable=invalid-overridden-method
        """Execute requests asynchronously."""
        req = self._execute(request)
        if self.params.broadcast_enable and not request.unit_id:
            resp = b"Broadcast write sent - no response expected"
        else:
            resp = await asyncio.wait_for(req, timeout=self.params.timeout)
        return resp

    def connection_made(self, transport):
        """Call when a connection is made.

        The transport argument is the transport representing the connection.
        """
        self.transport = transport
        self._connection_made()

        if self.factory:
            self.factory.protocol_made_connection(self)  # pylint: disable=no-member,useless-suppression

    def connection_lost(self, reason):
        """Call when the connection is lost or closed.

        The argument is either an exception object or None
        """
        self.transport = None
        self._connection_lost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(self)  # pylint: disable=no-member,useless-suppression

    def data_received(self, data):
        """Call when some data is received.

        data is a non-empty bytes object containing the incoming data.
        """
        self._data_received(data)

    def create_future(self):
        """Help function to create asyncio Future object."""
        return asyncio.Future()

    def resolve_future(self, my_future, result):
        """Resolve the completed future and sets the result."""
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

    def write_transport(self, packet):
        """Write transport."""
        if self.use_udp:
            return self.transport.sendto(packet)
        return self.transport.write(packet)

    def _execute(self, request, **kwargs):  # pylint: disable=unused-argument
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
