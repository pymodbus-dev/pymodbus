"""Modbus Client Common.

This is a common client mixin that can be used by
both the synchronous and asynchronous clients to
simplify the interface.
"""
# pylint: disable=missing-type-doc
import asyncio
import logging

from pymodbus.utilities import hexlify_packets
from pymodbus.exceptions import ConnectionException
from pymodbus.client.base import ModbusBaseClient

_logger = logging.getLogger(__name__)


class ModbusClientProtocol(
    ModbusBaseClient,
    asyncio.Protocol,
    asyncio.DatagramProtocol
):
    """Asyncio specific implementation of asynchronous modbus client protocol."""

    #: Factory that created this instance.
    factory = None
    transport = None
    use_udp = False

    def __init__(
        self,
        source_address=None,
        use_udp=False,
        **kwargs
    ):
        """Initialize a Modbus TCP/UDP asynchronous client

        :param host: Host IP address
        :param port: Port
        :param framer: Framer to use
        :param source_address: Specific to underlying client being used
        :param timeout: Timeout in seconds
        :param kwargs: Extra arguments
        """
        self.use_udp = use_udp
        self._connected = False
        super().__init__(**kwargs)

        self.source_address = source_address or ("", 0)

    async def execute(self, request=None):  # pylint: disable=invalid-overridden-method
        """Execute requests asynchronously.

        :param request:
        :return:
        """
        req = self._execute(request)
        if self.params.broadcast_enable and not request.unit_id:
            resp = b"Broadcast write sent - no response expected"
        else:
            resp = await asyncio.wait_for(req, timeout=self.params.timeout)
        return resp

    def connection_made(self, transport):
        """Call when a connection is made.

        The transport argument is the transport representing the connection.

        :param transport:
        """
        self.transport = transport
        self._connection_made()

        if self.factory:
            self.factory.protocol_made_connection(self)  # pylint: disable=no-member,useless-suppression

    def connection_lost(self, reason):
        """Call when the connection is lost or closed.

        The argument is either an exception object or None

        :param reason:
        """
        self.transport = None
        self._connection_lost(reason)

        if self.factory:
            self.factory.protocol_lost_connection(self)  # pylint: disable=no-member,useless-suppression

    def data_received(self, data):
        """Call when some data is received.

        data is a non-empty bytes object containing the incoming data.

        :param data:
        """
        self._data_received(data)

    def create_future(self):
        """Help function to create asyncio Future object."""
        return asyncio.Future()

    def resolve_future(self, my_future, result):
        """Resolve the completed future and sets the result.

        :param my_future:
        :param result:
        """
        if not my_future.done():
            my_future.set_result(result)

    def raise_future(self, my_future, exc):
        """Set exception of a future if not done.

        :param my_future:
        :param exc:
        """
        if not my_future.done():
            my_future.set_exception(exc)

    def _connection_made(self):
        """Call upon a successful client connection."""
        _logger.debug("Client connected to modbus server")
        self._connected = True

    def _connection_lost(self, reason):
        """Call upon a client disconnect

        :param reason: The reason for the disconnect
        """
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
        """Get response, check for valid message, decode result

        :param data: The data returned from the server
        """
        txt = f"recv: {hexlify_packets(data)}"
        _logger.debug(txt)
        unit = self.framer.decode_data(data).get("unit", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)

    def _handle_response(self, reply, **kwargs):  # pylint: disable=unused-argument
        """Handle the processed response and link to correct deferred

        :param reply: The reply to process
        :param kwargs: The rest
        """
        if reply is not None:
            tid = reply.transaction_id
            if handler := self.transaction.getTransaction(tid):
                self.resolve_future(handler, reply)
            else:
                txt = f"Unrequested message: {str(reply)}"
                _logger.debug(txt)

    def _build_response(self, tid):
        """Return a deferred response for the current request.

        :param tid: The transaction identifier for this response
        :returns: A defer linked to the latest request
        """
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

    def datagram_received(self, data, addr):
        """Receive datagram."""
        self._data_received(data)
