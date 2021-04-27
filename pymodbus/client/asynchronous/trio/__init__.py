"""
Implementation of a Modbus Client using Trio
--------------------------------------------
"""
import functools
import logging

import async_generator
import trio

from pymodbus.client.asynchronous.mixins import AsyncModbusClientMixin
from pymodbus.exceptions import ConnectionException
from pymodbus.utilities import hexlify_packets

_logger = logging.getLogger(__name__)


class _EventAndValue:
    """
    A helper class for translating between the existing callback idioms and
    those of Trio.
    """
    def __init__(self):
        self.event = trio.Event()
        self.value = self

    def set(self, value):
        """Assign a value and set the underlying trio event."""
        self.value = value
        self.event.set()


class BaseModbusAsyncClientProtocol(AsyncModbusClientMixin):
    """
    Trio specific implementation of the asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None

    def _build_packet(self, request):
        request.transaction_id = self.transaction.getNextTID()
        return self.framer.buildPacket(request)

    async def execute(self, request=None):
        """
        Executes requests asynchronously
        :param request:
        :return:
        """
        packet = self._build_packet(request=request)
        _logger.debug("send: " + hexlify_packets(packet))
        # TODO: should we retry on trio.BusyResourceError?
        await self.transport.send_all(packet)
        with trio.fail_after(seconds=1):
            response = await self._build_response(request.transaction_id)
        return response

    def connection_made(self, transport):
        """
        Called when a connection is made.

        The transport argument is the transport representing the connection.
        :param transport:
        :return:
        """
        self.transport = transport
        _logger.debug("Client connected to modbus server")
        self._connected = True

        if self.factory:
            self.factory.protocol_made_connection(self)

    # TODO: _connectionLost looks like functionality to have somewhere

    def _data_received(self, data):
        """
        Get a response, check for a valid message, decode the result.

        :param data: The data returned from the server
        """
        _logger.debug("recv: " + hexlify_packets(data))

        decoded = self.framer.decode_data(data)

        unit = decoded.get("unit", 0)
        self.framer.processIncomingPacket(data, self._handle_response, unit=unit)
        self.data = b''

    def _handle_response(self, reply, **kwargs):
        """
        Handle the processed response and link to correct deferred.

        :param reply: The reply to process
        """
        if reply is not None:
            tid = reply.transaction_id
            handler = self.transaction.getTransaction(tid)
            if handler:
                handler(reply)
            else:
                _logger.debug("Unrequested message: " + str(reply))

    async def _build_response(self, tid):
        """
        Helper method to wait for and collect the result of the passed
        transaction ID.

        :param tid: The transaction identifier for this response
        :returns: The decoded response.
        """
        if not self._connected:
            raise ConnectionException('Client is not connected')

        event_and_value = _EventAndValue()
        self.transaction.addTransaction(event_and_value.set, tid)
        await event_and_value.event.wait()
        return event_and_value.value


class ModbusTcpClientProtocol(BaseModbusAsyncClientProtocol):
    """
    Trio specific implementation of the asynchronous modbus client protocol.
    """

    #: Factory that created this instance.
    factory = None
    transport = None

    def data_received(self, data):
        """
        Called when some data is received.
        data is a non-empty bytes object containing the incoming data.
        :param data:
        :return:
        """
        self._data_received(data)


# TODO: implement UDP


class TrioModbusTcpClient:
    """Client to connect to a modbus device over TCP/IP."""

    def __init__(self, host=None, port=502, protocol_class=None):
        """
        Initializes a Trio Modbus Tcp Client
        :param host: Host IP address
        :param port: Port to connect
        :param protocol_class: Protocol used to talk to modbus device.
        """
        #: Protocol used to talk to modbus device.
        self.protocol_class = protocol_class or ModbusTcpClientProtocol
        #: Current protocol instance.
        self.protocol = None

        self.host = host
        self.port = port

        self.connected = False

    @async_generator.asynccontextmanager
    async def manage_connection(self):
        """
        Create a context manager to open the connection to the server and
        close it when leaving the context block.
        :return:
        """
        async with trio.open_nursery() as nursery:
            self.protocol = self._create_protocol()
            client_stream = await trio.open_tcp_stream(self.host, self.port)

            self.protocol.connection_made(transport=client_stream)
            nursery.start_soon(
                functools.partial(self._receiver, stream=client_stream),
            )

            yield self.protocol

            nursery.cancel_scope.cancel()

    async def _receiver(self, stream):
        """
        Process incoming raw stream data.
        :return:
        """
        async for data in stream:
            self.protocol.data_received(data)

    def stop(self):
        """
        Stop the client.
        :return:
        """
        if self.connected:
            if self.protocol:
                if self.protocol.transport:
                    self.protocol.transport.close()

    def _create_protocol(self):
        """
        Factory function to create initialized protocol instance.
        :return: The initialized protocol
        """
        protocol = self.protocol_class()
        protocol.factory = self
        return protocol

    def protocol_made_connection(self, protocol):
        """
        Protocol notification of successful connection.
        :return:
        """
        _logger.info('Protocol made connection.')
        if not self.connected:
            self.connected = True
            self.protocol = protocol
        else:
            _logger.error('Factory protocol connect '
                          'callback called while connected.')


def init_tcp_client(proto_cls, host, port, **kwargs):
    """
    Helper function to initialize tcp client
    :param proto_cls:
    :param host:
    :param port:
    :param kwargs:
    :return:
    """
    client = TrioModbusTcpClient(protocol_class=proto_cls, host=host, port=port)
    return client
